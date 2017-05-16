use broadcast

DROP TABLE IF EXISTS data_type;

create table data_type
(
    type_id int NOT NULL unique key auto_increment COMMENT '類型編號', 
    type_name varchar(50) default ''  COMMENT '類型名稱', 
    type_dir varchar(300) default '' COMMENT '存放路徑',    
    type_weight double default 1 COMMENT '加權比重'
);

DROP TABLE IF EXISTS image_data;

create table image_data
(
    img_id varchar(14) unique key,
    type_id int default 1,
    img_system_name varchar(50) not null,
    img_thumbnail_name varchar(50) not null,
    img_file_name varchar(50) not null,
    img_upload_time datetime default now(),
    img_start_date date not null,
    img_end_date date not null,
    img_start_time time default '00:00:00',
    img_end_time time default '23:59:59',
    img_display_count int default 0,
    img_display_time int default 5,
    img_is_expire bit(1) default 0,
    user_id int not null,
    img_last_edit_user_id int default 0,
    img_is_delete bit(1) default 0,
    img_like_count int default 0
);

DROP TABLE IF EXISTS user;

create table user
(
    user_id int NOT NULL unique key auto_increment ,
    user_name varchar(50) not null,
    user_password varchar(360) not null,
    user_last_name varchar(50),
    user_first_name varchar(50),
    user_nickname varchar(50),
    user_join_date datetime default now(),
    user_email varchar(50),
    user_phone_number varchar(20) ,
    user_level int default 100,
    user_sex int default 0,
    user_enable bit(1) default 0,
    user_bluetooth_id varchar(50),
    user_profession int default 0 not null,
    user_birthday datetime
);

DROP TABLE IF EXISTS schedule;

create table schedule
(
    sche_sn int not null unique key auto_increment ,
    sche_id varchar(14) not null unique key,
    sche_target_id varchar(14) not null,
    sche_display_time int default 5,
    sche_arrange_time datetime default now(),
    sche_arrange_mode int not null, 
    sche_is_used bit(1) default 0,
    sche_is_artificial_edit bit(1) default 0    
);

DROP TABLE IF EXISTS text_data;

create table text_data
(
    text_id varchar(14) unique key,
    type_id int default 1,
    text_invisible_title varchar(100) not null,
    text_system_name varchar(50) not null,
    text_upload_time datetime default now(),
    text_start_date date not null,
    text_end_date date not null,
    text_start_time time default '00:00:00',
    text_end_time time default '23:59:59',
    text_display_count int default 0,
    text_display_time int default 5,
    text_is_expire bit(1) default 0,
    user_id int not null,
    text_last_edit_user_id int default 0,
    text_is_delete bit(1) default 0,
    text_like_count int default 0
);

DROP TABLE IF EXISTS arrange_mode;

create table arrange_mode
(
    armd_sn int unique key auto_increment,
    armd_mode int default 0,
    armd_condition varchar(100),
    armd_set_time datetime default now(),
    armd_start_time time default '00:00:00',
    armd_end_time time default '23:59:59',
    armd_is_expire bit(1) default 0,
    armd_is_delete bit(1) default 0
);


DROP TABLE IF EXISTS user_prefer;

create table user_prefer
(
        pref_id varchar(14) unique key,
        user_id int default 0,
        pref_data_type_01 varchar(100),
        pref_data_type_02 varchar(100),
        pref_data_type_03 varchar(100),
        pref_data_type_04 varchar(100),
        pref_data_type_05 varchar(100),
        pref_set_time datetime default now(),
        pref_is_delete bit(1) default 0
);
