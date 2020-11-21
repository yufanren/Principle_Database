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
        "Routes": page_routes,
        "Users": page_users,
        "Clubs": page_clubs,
        "Databse": getDB,
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
        "User stats": user_stat,
        "Score board": score_board,
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

#main page for showing all tables in database
def getDB():
    st.title('Database Information')
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
    sql_all_users = 'select * from user_score order by score desc'
    all_users = query_db(sql_all_users)
    all_users['rank'] = all_users['score'].rank(method = 'min', ascending = False)
    st.table(all_users)

#display user stats
def user_stat():
    sql_all_unames = 'select name from Users_membership order by name'
    all_unames = query_db(sql_all_unames)['name'].tolist()
    uname_sel = st.selectbox('Choose a user', all_unames)

    if uname_sel:
        user_info = query_db("select * from Users_membership where name = {};".format('\'' + uname_sel + '\''))
        user_info_str = '  '.join([uname_sel, 'User ID: ' + str(user_info['userid'].values[0]), 'DOB: ' + str(user_info['dob'].values[0]), 'Club: ' + user_info['club'].values[0]])    
        st.markdown(f"<h3 style='text-align: center; color: black;'>{user_info_str}</h3>", unsafe_allow_html=True)

        user_ascends = query_db("select RAD.name, ascend_date from (select name, UM.userid, ascend_date, UAR.rtid from Users_membership UM left outer join Users_Ascend_Routes UAR on UM.userid = UAR.userid where name = {}) UA left outer join Routes_have_Area_Discipline RAD on UA.rtid = RAD.rtid where RAD.name is not null;".format('\'' + uname_sel + '\''))
        todo_list = query_db("select RAD.name from (select ToDo_List.rtid from Users_membership UM left outer join ToDo_List on UM.userid = ToDo_List.userid where name = {}) UL left outer join Routes_have_Area_Discipline RAD on UL.rtid = RAD.rtid where RAD.name is not null;".format('\'' + uname_sel + '\''))['name'].tolist()
        partners_list = query_db("select name from (select climber2 as climber from Users_membership UM, Partners P where UM.userid = P.climber1 and name = {} union select climber1 as climber from Users_membership UM, Partners P where UM.userid = P.climber2 and name = {}) C, Users_membership UM where C.climber = UM.userid order by name".format('\'' + uname_sel + '\'', '\'' + uname_sel + '\''))['name'].tolist()
        
        ascendRt = user_ascends['name'].tolist()
        ascendDate = user_ascends['ascend_date'].tolist()
        ascendList = []
        for i in range(len(ascendRt)):
            ascendList.append(ascendRt[i] + '  ' + str(ascendDate[i]))

        row_num = max(len(todo_list), len(partners_list), len(ascendList))
        todo_list.extend([' ' for i in range(row_num - len(todo_list))])
        partners_list.extend([' ' for i in range(row_num - len(partners_list))])
        ascendList.extend([' ' for i in range(row_num - len(ascendList))])

        df_usr = {
            'ascends': ascendList,
            'todo list': todo_list,
            'partners': partners_list
        }
        st.table(df_usr)

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
main()