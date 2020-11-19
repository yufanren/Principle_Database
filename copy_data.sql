
/*copy data*/
COPY Areas from 
'/home/yufan/Public/CSV/Areas.csv'
delimiter ',' CSV HEADER;

COPY Disciplines from 
'/home/yufan/Public/CSV/Disciplines.csv'
delimiter ',' CSV HEADER;

COPY Features from 
'/home/yufan/Public/CSV/Features.csv'
delimiter ',' CSV HEADER;

COPY Routes_have_Area_Discipline (name, length, area, discipline)
from '/home/yufan/Public/CSV/Routes_have_Area_Discipline.csv'
delimiter ',' CSV HEADER;

COPY Routes_have_Features from 
'/home/yufan/Public/CSV/Routes_have_Features.csv'
delimiter ',' CSV HEADER;

COPY Clubs from 
'/home/yufan/Public/CSV/Clubs.csv'
delimiter ',' CSV HEADER;

COPY Users_membership (name, dob, club)
from '/home/yufan/Public/CSV/Users_membership.csv'
delimiter ',' CSV HEADER;

COPY Partners from 
'/home/yufan/Public/CSV/Partners.csv'
delimiter ',' CSV HEADER;

COPY Trips_Organized from 
'/home/yufan/Public/CSV/Trips_Organized.csv'
delimiter ',' CSV HEADER;

COPY Dates from 
'/home/yufan/Public/CSV/Dates.csv'
delimiter ',' CSV HEADER;

COPY Users_Ascend_Routes from 
'/home/yufan/Public/CSV/Users_Ascend_Routes.csv'
delimiter ',' CSV HEADER;

COPY ToDo_List from 
'/home/yufan/Public/CSV/ToDo_List.csv'
delimiter ',' CSV HEADER;

COPY Ratings (difficulty, quality, user_comment, comment_time, commenter, route) from 
'/home/yufan/Public/CSV/Ratings.csv'
delimiter ',' CSV HEADER;


create materialized view rt_rating as 
select rtid, round(avg(quality), 1) quality, round(avg(difficulty), 1) difficulty
from Routes_have_Area_Discipline left outer join Ratings
on rtid = route
group by rtid
order by rtid;

create materialized view user_score as 
select userid, name, round(coalesce(sum(((count - 1) * 0.25 + 1) * difficulty), 0), 1) score
from (select UM.userid, name, rtid, count(rtid) count
      from Users_membership UM left outer join Users_Ascend_Routes UAR
      on UM.userid = UAR.userid
      group by UM.userid, name, rtid) UR left outer join rt_rating RR
on UR.rtid = RR.rtid
group by userid, name
order by userid;