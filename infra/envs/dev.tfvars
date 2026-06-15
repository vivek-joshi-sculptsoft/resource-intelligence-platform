environment       = "dev"
ec2_instance_type = "t3.small"
ec2_key_pair_name = "ri-platform-dev"
ec2_volume_size   = 30
admin_ssh_cidr    = "0.0.0.0/0" # Restrict to your IP in production

db_instance_class = "db.t4g.micro"
db_name           = "ri_platform"
db_username       = "ripadmin"
db_password       = "CHANGE_ME_dev_password_2026"
db_storage_gb     = 20
db_max_storage_gb = 50

domain_name     = ""
route53_zone_id = ""
