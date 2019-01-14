use github;

create table issues(
issue_id INT NOT NULL auto_increment primary key,
repo_id int,
tag varchar(10),
issue_num int,
reporter_id INT,
assignees_id varchar(60),
reviewers_id varchar(60),
title text,
body longtext,
state int,
created_at varchar(20),
closed_at varchar(20),
merged_at varchar(20),
db_role varchar(20)
);

create table comments(
comment_id INT NOT NULL auto_increment primary key,
repo_id int,
issue_num int,
user_id int,
body longtext,
created_at varchar(20),
db_role varchar(20)
);
