import streamlit as st
import pandas as pd
import psycopg2
from configparser import ConfigParser

#get database log info from database.ini file
@st.cache
def get_config(filename='database.ini', section='postgresql'):
    parser = ConfigParser()
    parser.read(filename)
    return {k: v for k, v in parser.items(section)}

#query database and return result as pandas dataframe
def query_db(sql: str):
    db_info = get_config()
    conn = psycopg2.connect(**db_info)
    cur = conn.cursor()
    cur.execute(sql)
    data = cur.fetchall()
    column_names = [desc[0] for desc in cur.description]
    conn.commit()
    cur.close()
    conn.close()
    df = pd.DataFrame(data=data, columns=column_names)
    return df


def main():
    prepDB();
    pages = {
        "User Information": page_users,
        "Area Information": page_areas,
        "Route Information": page_routes,
        "Club Information": page_clubs,
        "Database Information": getDB,
    }

    st.sidebar.title("Select task")
    page = st.sidebar.radio("What are you interested in?", tuple(pages.keys()))

    pages[page]()

#main page for routes info
def page_routes():
    st.title('Routes Information')
    options = {
    "Check out routes": show_routes,
    "Look for routes by location and discipline": query_routes,
    "Look for routes by ratings": rt_by_ratings,
    }
    query_rts = st.radio("Choose query method", tuple(options.keys()))
    options[query_rts]()

#main page for users info
def page_users():
    st.title('User Information')
    pages = {
        "Overall User Rankings": score_board,
        "Individual User Statistics": user_stat,  
    }
    user_options = st.radio("Choose query mode", tuple(pages.keys()))
    pages[user_options]()

#main page for clubs info
def page_clubs():
    st.title('Club Information')
    sql_all_clubs = 'select * from Clubs order by name;'
    all_clubs = query_db(sql_all_clubs)
    all_club_names = all_clubs['name'].tolist()
    club_name = st.selectbox('Choose a club', all_club_names)

    club_row = all_clubs.loc[all_clubs['name'] == club_name]
    st.write(f"{club_row['name'].values[0]} was founded in {club_row['year_founded'].values[0]} at {club_row['location'].values[0]}.")#

    options = ["Trips hosted", "Club members"]
    query_clubs = st.radio("What would you like to know?", options)
    if query_clubs == 'Trips hosted':
        sql_club_info = "select name, start_date, area from Trips_Organized where organizer = {} order by start_date;".format('\'' + club_name + '\'')
    elif query_clubs == "Club members":
        sql_club_info = "select userid, name, dob from Users_membership where club = {} order by userid;".format('\'' + club_name + '\'')
    club_info = query_db(sql_club_info)
    st.table(club_info)

# main page for area information
def page_areas():
    st.title("Area Information")
    all_countries = query_db('select distinct country from Areas order by country;')
    country_names = all_countries['country'].tolist()
    country_select = st.selectbox('Find Areas by Country', country_names)

    if country_select:
        area_sql = "select R.area, R.total_routes, SR.sport_routes, TR.trad_routes, B.boulder_routes from (select RAD.area, count(rtid) as total_routes from Areas A, Routes_have_Area_Discipline RAD where A.country = '{}' and RAD.area = A.name group by RAD.area) R left join (select RAD.area, count(rtid) as sport_routes from Areas A, Routes_have_Area_Discipline RAD where A.country = '{}' and RAD.area = A.name and RAD.discipline = 'Sport' group by RAD.area) SR on R.area = SR.area left join (select RAD.area, count(rtid) as trad_routes from Areas A, Routes_have_Area_Discipline RAD where A.country = '{}' and RAD.area = A.name and RAD.discipline = 'Traditional' group by RAD.area) TR on R.area = TR.area left join (select RAD.area, count(rtid) as boulder_routes from Areas A, Routes_have_Area_Discipline RAD where A.country = '{}' and RAD.area = A.name and RAD.discipline = 'Boulder' group by RAD.area) B on R.area = B.area;".format(country_select, country_select, country_select, country_select)
        area_list = query_db(area_sql)
        st.table(area_list)

    area_input = st.text_input("Search Areas: ")

    if area_input:

        f'Choose Disciplines:'
        typeSport = st.checkbox("Sport", value=True)
        typeTrad = st.checkbox("Traditional", value=True)
        typeBoulder = st.checkbox("Boulder", value=True)
        typeOther = st.checkbox("Other", value=True)

        curr_discipline = []

        if typeSport:
            curr_discipline.append("Sport")
        if typeTrad:
            curr_discipline.append("Traditional")
        if typeBoulder:
            curr_discipline.append("Boulder")
        if typeOther:
            curr_discipline.append("Ice")
            curr_discipline.append("Mixed")

        grade_count_sql = ""

        # Order ascents based on column choice
        order_choice = st.selectbox('Order Routes By:', ["Name", "Discipline", "Difficulty", "Quality"])
        if (order_choice == "Difficulty" or order_choice == "Quality"):
            curr_order = order_choice + " DESC"
        else :
            curr_order = order_choice

        f'List of Routes at {area_input}'

        curr_query = ""
        for i in range (len(curr_discipline)):
            curr_query += "select AR.name, AR.discipline, AR.length, RR.difficulty, RR.quality from (select A.name as area, RAD.rtid, RAD.name, RAD.discipline, RAD.length from Areas A, Routes_have_Area_Discipline RAD where A.name = RAD.area and A.name = '{}' and RAD.discipline = '{}') AR, rt_rating RR where AR.rtid = RR.rtid".format(area_input, curr_discipline[i])
            if i < (len(curr_discipline) - 1):
                curr_query += " UNION "
            else:
                curr_query += " order by {};".format(curr_order)

        if (curr_query != ""):
            area_stats = query_db(curr_query)
            st.table(area_stats)



#main page for showing all tables in database
def getDB():
    st.title('Database Tables (Raw)')
    sql_all_table_names = "select relname from pg_class where relkind='r' and relname !~ '^(pg_|sql_)' order by relname;"
    all_table_names = query_db(sql_all_table_names)['relname'].tolist()
    table_name = st.selectbox('Choose a table', all_table_names)
    if table_name:
        f'Display the table'
 
    sql_table = f'select * from {table_name};'
    df = query_db(sql_table)
    st.table(df)

#display user rankings based on scores earned
def score_board():
    f'User Rankings Based on Routes Ascended (quantity and difficulty)'
    sql_all_users = 'select name, userid, score from user_score order by score desc'
    all_users = query_db(sql_all_users)
    all_users['rank'] = all_users['score'].rank(method = 'min', ascending = False)
    st.table(all_users)

#display user stats
def user_stat():
    sql_all_unames = 'select distinct name from Users_membership order by name'
    all_unames = query_db(sql_all_unames)['name'].tolist()
    uname_sel = st.text_input('Search Users (Some sample users: Ashima, Jimmy, Sasha, Dai)')

    if uname_sel:
        user_info = query_db("select * from Users_membership where name = {};".format('\'' + uname_sel + '\''))
        for i in range (len(user_info.index)):

            user_info_str = '  '.join([uname_sel, ',  User ID: ' + str(user_info['userid'].values[i]), ',  DOB: ' + str(user_info['dob'].values[i]), ',  Club: ' + (user_info['club'].values[i] if user_info['club'].values[i] is not None else ' ')])    
            st.markdown(f"<h3 style='text-align: center; color: black;'>{user_info_str}</h3>", unsafe_allow_html=True)

            uid = user_info['userid'].values[i]

            # Basic statistics on this climber
            f"{uname_sel}'s Ascent Totals by Difficulty:"
            sql_ascents = "select RR.difficulty, count (RR.rtid) as ascent_count from Users_Ascend_Routes UAR, rt_rating RR where UAR.rtid = RR.rtid and UAR.userid = {} and RR.difficulty > 0 group by RR.difficulty order by RR.difficulty DESC;".format(uid)
            ascent_breakdown = query_db(sql_ascents)
            st.table(ascent_breakdown)

    
            # View different lists for individual climber
            choices = {
            "Ascent List": user_ascents,
            "To Do List": user_toDos,
            "Partner List": user_partners,
            "Areas Visited": user_areas
            }
            
            user_choices = st.radio(uname_sel + "'s Climbing Lists:", tuple(choices.keys()), key = str(uid))
            choices[user_choices](uid)


#query routes ascended by a user
def user_ascents(userid):

    f'Choose Ascent Disciplines:'
    typeSport = st.checkbox("Sport", value=True, key=str(userid))
    typeTrad = st.checkbox("Traditional", value=True, key=str(userid))
    typeBoulder = st.checkbox("Boulder", value=True, key=str(userid))
    typeOther = st.checkbox("Other", value=True, key=str(userid))

    curr_discipline = []

    if typeSport:
        curr_discipline.append("Sport")
    if typeTrad:
        curr_discipline.append("Traditional")
    if typeBoulder:
        curr_discipline.append("Boulder")
    if typeOther:
        curr_discipline.append("Ice")
        curr_discipline.append("Mixed")


    # Order ascents based on column choice
    order_choice = st.selectbox('Order Ascents By:', ["Name", "Area", "Discipline", "Difficulty", "Quality", "Date"], key=str(userid))
    if order_choice == "Date":
        curr_order = "ascend_date DESC"
    elif (order_choice == "Difficulty" or order_choice == "Quality"):
        curr_order = order_choice + " DESC"
    else :
        curr_order = order_choice


    curr_query = ""
    for i in range (len(curr_discipline)):
        curr_query += "select UA.name, UA.area, UA.discipline, RR.difficulty, RR.quality, UA.ascend_date from (select UAR.userid, UAR.rtid, RAD.name, RAD.area, RAD.discipline, UAR.ascend_date from Users_Ascend_Routes UAR, Routes_have_Area_Discipline RAD where UAR.rtid = RAD.rtid and UAR.userid = {} and RAD.discipline = '{}') UA, rt_rating RR where UA.rtid = RR.rtid".format(userid, curr_discipline[i])
        if i < (len(curr_discipline) - 1):
            curr_query += " UNION "
        else:
            curr_query += " order by {};".format(curr_order)

    if (curr_query != ""):
        ascent_list = query_db(curr_query)
        st.table(ascent_list)


#query routes on a users to do list
def user_toDos(userid):
    curr_order = st.selectbox('Order To Do List By:', ["Name", "Area", "Discipline", "Difficulty", "Quality"], key=str(userid))
    if (curr_order == "Difficulty" or curr_order == "Quality"):
        curr_order += " DESC"

    toDo_list = query_db("select UA.name, UA.area, UA.discipline, RR.difficulty, RR.quality from (select UAR.userid, UAR.rtid, RAD.name, RAD.area, RAD.discipline from ToDo_List UAR, Routes_have_Area_Discipline RAD where UAR.rtid = RAD.rtid and UAR.userid = {}) UA, rt_rating RR where UA.rtid = RR.rtid order by {};".format(userid, curr_order))
    st.table(toDo_list)

#query user partners
def user_partners(userid):
    partners_list = query_db("select name, dob, club from (select climber2 as climber from Users_membership UM, Partners P where UM.userid = P.climber1 and UM.userid = {} UNION select climber1 as climber from Users_membership UM, Partners P where UM.userid = P.climber2 and UM.userid = {}) C, Users_membership UM where C.climber = UM.userid order by name;".format(userid, userid))
    st.table(partners_list)

#query user areas
def user_areas(userid):
    area_list = query_db("select A.name, A.country from (select distinct area from Users_Ascend_Routes UAR, Routes_have_Area_Discipline RAD where UAR.rtid = RAD.rtid and UAR.userid = {}) UA, Areas A where UA.area = A.name order by country;".format(userid))
    st.table(area_list)


#query routes by rating
def rt_by_ratings():
    rating_radio = st.radio("Lookup by:", (["Quality" , "Difficulty"]))
    rating_slider = st.slider("Choose quality rating", 1, 10, step =  1, key = 'rating')

    if rating_radio and rating_slider:
        mode = 'quality' if rating_radio == 'Quality' else 'difficulty' 

        f'Routes with chosen quality or difficulty rating'
        sql_rt_rating = "select RT.rtid, name, length, area, discipline, features, quality, difficulty from (select rtid, name, length, area, discipline, coalesce (STRING_AGG(feature, ' '), ' ') features from Routes_have_Area_Discipline left outer join Routes_have_Features on rtid = route group by rtid ) RT, rt_rating where RT.rtid = rt_rating.rtid and {} = {} order by rtid;".format(mode, rating_slider)
        rt_list = query_db(sql_rt_rating)
        st.table(rt_list)

#query routes by route name
def show_routes():
    sql_all_routes = 'select distinct name from Routes_have_Area_Discipline order by name;'
    all_routes = query_db(sql_all_routes)['name'].tolist()
    rt_names = st.multiselect('Choose a route', all_routes, key = 'rt')
    if rt_names:
        rt_mulsel_str = ','.join(["'" + rt + "'" for rt in rt_names])
        sql_rt = f"select RT.rtid, name, length, area, discipline, features, quality, difficulty from (select rtid, name, length, area, discipline, coalesce (STRING_AGG(feature, ' '), ' ') features from Routes_have_Area_Discipline left outer join Routes_have_Features on rtid = route where name in ({rt_mulsel_str}) group by rtid ) RT, rt_rating where RT.rtid = rt_rating.rtid order by rtid;"
        rt_list = query_db(sql_rt)
        st.table(rt_list)
        
#query routes by area and discipline
def query_routes():
    sql_all_areas = 'select name from Areas order by name;'
    all_areas = query_db(sql_all_areas)['name'].tolist()
    area_names = st.multiselect('Choose a area', all_areas, key = 'area')

    sql_all_discipline = 'select name from Disciplines order by name;'
    all_disciplines = query_db(sql_all_discipline)['name'].tolist()
    discipline_names = st.multiselect('Choose a discipline', all_disciplines, key = 'discipline')

    if area_names and discipline_names:
        area_mulsel_str = ','.join(["'" + area + "'" for area in area_names])
        discipline_mulsel_str = ','.join(["'" + disc + "'" for disc in discipline_names])
        sql_rt = f"select RT.rtid, name, length, area, discipline, features, quality, difficulty from (select rtid, name, length, area, discipline, coalesce (STRING_AGG(feature, ' '), ' ') features from Routes_have_Area_Discipline left outer join Routes_have_Features on rtid = route where area in ({area_mulsel_str}) and discipline in ({discipline_mulsel_str}) group by rtid ) RT, rt_rating where RT.rtid = rt_rating.rtid order by rtid;"
        rt_list = query_db(sql_rt)
        st.table(rt_list)

#refresh materialzed view on database server
def prepDB():
    db_info = get_config()
    conn = psycopg2.connect(**db_info)
    cur = conn.cursor()
    cur.execute("refresh materialized view rt_rating;refresh materialized view user_score;")
    conn.commit()
    cur.close()
    conn.close()
    st.markdown("""
    <style>
    table td:nth-child(1) {
        display: none
    }
    table th:nth-child(1) {
        display: none
    }
    </style>
    """, unsafe_allow_html=True)

#make dataframe from lists with unequal sizes, for side-by-side display
#can use streamlit.beta_columns instead after version 0.68
def makeTable(**kwargs):
	max_row = max(len(i) for i in kwargs.values())
	for v in kwargs.values():
		v.extend([' ' for i in range(max_row - len(v))])
	return {k:kwargs[k] for k in kwargs}	

main()
