drop table if exists ToDo_List cascade;
drop table if exists Users_Ascend_Routes cascade;
drop table if exists Dates cascade;
drop table if exists Ratings cascade;
drop table if exists Trips_Organized cascade;
drop table if exists Partners cascade;
drop table if exists Users_membership cascade;
drop table if exists Clubs cascade;
drop table if exists Routes_have_Features cascade;
drop table if exists Routes_have_Area_Discipline cascade;
drop table if exists Features cascade;
drop table if exists Disciplines cascade;
drop table if exists Areas cascade;

create table Areas (
	name varchar(32) primary key,
	country varchar(32),
	latitude real,
	longitude real
);

create table Disciplines (
	name varchar(32) primary key
);

create table Features (
	name varchar(32) primary key
);

create table Routes_have_Area_Discipline ( 
	rtid serial primary key,
	name varchar(32),
	length real,
	area  varchar(32) not null,
	discipline varchar(32) not null,
	foreign key (area) references Areas (name),
	foreign key (discipline) references Disciplines (name)
);

create table Routes_have_Features (
	route int,
	feature varchar(32),
	primary key (route, feature),
	foreign key (route) references Routes_have_Area_Discipline (rtid),
	foreign key (feature) references Features (name)
);

create table Clubs (
	name varchar(32) primary key,
	year_founded int,	
	location varchar(128)
);

create table Users_membership (
	userid serial primary key,
	name varchar(32),
	dob date,
	club varchar(32),
	foreign key (club) references Clubs (name)
);

create table Partners (
	climber1 int,
	climber2 int,
	primary key (climber1, climber2),
	foreign key (climber1) references Users_membership (userid),
	foreign key (climber2) references Users_membership (userid)
);

create table Trips_Organized (
	name varchar(32),
	start_date date,
	primary key (name, start_date),
	organizer varchar(32) not null,
	area varchar(32) not null,
	foreign key (organizer) references Clubs (name),
	foreign key (area) references Areas (name)
);

create table Ratings (
	rid serial primary key,
	difficulty int not null check (difficulty >= 1 and difficulty <= 10),
	quality int not null check (quality >= 1 and quality <= 10),
	user_comment varchar(256),	
	comment_time time not null,
	commenter int not null,
	route int not null,
	foreign key (commenter) references Users_membership (userid),
	foreign key (route) references Routes_have_Area_Discipline (rtid) 
);

create table Dates (
	ascend_date date primary key
);

create table Users_Ascend_Routes (
	userid int,
	rtid int,
	ascend_date date,
	primary key (userid, rtid, ascend_date),
	foreign key (userid) references Users_membership (userid),
	foreign key (rtid) references Routes_have_Area_Discipline (rtid),
	foreign key (ascend_date) references Dates (ascend_date)
);

create table ToDo_List (
	userid int,
	rtid int,
	primary key (userid, rtid),
	foreign key (userid) references Users_membership (userid),
	foreign key (rtid) references Routes_have_Area_Discipline (rtid)
);
