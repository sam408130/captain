#-*- coding: utf-8 -*-

database_name = 'shangxin'
development_database_name = 'shangxin_db_dev'
distribution_database_name = 'shangxin_db'


#一手专题
yishou_activity_table = 'yishou_activity'
#一手专题列表
yishou_activity_detail_table = 'yishou_activity_detail'
#一手商品
yishou_item_table = 'yishou_item'


#天天专题
tt_activity_table = 'tt_activity'
#天天专题列表
tt_activity_detail_table = 'tt_activity_detail'
#天天商品
tt_item_table = 'tt_item'




database_config = {
	'host': 'localhost',
	'port': 3306,
	'user': 'root',
	'password': '123456',
}


development_database_config = {
	'host': 'rm-2zezcg73nb7l49k2eo.mysql.rds.aliyuncs.com',
	'port': 3306,
	'user': 'db_user_dev',
	'password': 'db-user-dev8',
}


distribution_database_config = {
	'host': 'rm-2ze57e72f84zit045.mysql.rds.aliyuncs.com',
	'port': 3306,
	'user': 'shangxin_db_user',
	'password': 'shangxin_db_user0801',
}
