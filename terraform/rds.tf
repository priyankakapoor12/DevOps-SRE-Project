# RDS PostgreSQL for Task Manager Application

# Security Group for RDS
resource "aws_security_group" "rds" {
  name        = "${var.cluster_name}-rds-sg"
  description = "Security group for RDS PostgreSQL"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description = "PostgreSQL from VPC"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [module.vpc.vpc_cidr_block]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.cluster_name}-rds-sg"
  }
}

# DB Subnet Group (uses private subnets)
resource "aws_db_subnet_group" "main" {
  name       = "${var.cluster_name}-db-subnet"
  subnet_ids = module.vpc.private_subnets

  tags = {
    Name = "${var.cluster_name}-db-subnet"
  }
}

# RDS PostgreSQL Instance
resource "aws_db_instance" "taskmanager" {
  identifier     = "${var.cluster_name}-db"
  engine         = "postgres"
  engine_version = "15"
  instance_class = "db.t3.micro"

  allocated_storage     = 20
  max_allocated_storage = 100
  storage_type          = "gp3"
  storage_encrypted     = true

  db_name  = "taskmanager"
  username = "taskadmin"
  password = var.db_password

  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name

  # Backup configuration
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "Mon:04:00-Mon:05:00"

  # For demo - set to false/true for production
  skip_final_snapshot = true
  deletion_protection = false

  # Performance Insights (free tier)
  performance_insights_enabled = true
  performance_insights_retention_period = 7

  tags = {
    Name        = "${var.cluster_name}-db"
    Environment = "demo"
  }
}

# Outputs
output "rds_endpoint" {
  description = "RDS endpoint"
  value       = aws_db_instance.taskmanager.endpoint
}

output "rds_hostname" {
  description = "RDS hostname (without port)"
  value       = aws_db_instance.taskmanager.address
}

output "rds_port" {
  description = "RDS port"
  value       = aws_db_instance.taskmanager.port
}

output "rds_database_name" {
  description = "Database name"
  value       = aws_db_instance.taskmanager.db_name
}

output "rds_username" {
  description = "Database username"
  value       = aws_db_instance.taskmanager.username
}

output "database_url" {
  description = "Full DATABASE_URL for application"
  value       = "postgresql://${aws_db_instance.taskmanager.username}:${var.db_password}@${aws_db_instance.taskmanager.endpoint}/${aws_db_instance.taskmanager.db_name}"
  sensitive   = true
}
