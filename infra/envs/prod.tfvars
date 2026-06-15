environment       = "prod"
ec2_instance_type = "t3.small"
ec2_key_pair_name = "ri-platform-prod"
ec2_volume_size   = 30
admin_ssh_cidr    = "YOUR_OFFICE_IP/32" # Replace with actual admin IP

db_instance_class = "db.t4g.micro"
db_name           = "ri_platform"
db_username       = "ripadmin"
db_password       = "CHANGE_ME_prod_password_2026"
db_storage_gb     = 20
db_max_storage_gb = 100

# Set these when custom domain is ready
domain_name     = ""
route53_zone_id = ""
