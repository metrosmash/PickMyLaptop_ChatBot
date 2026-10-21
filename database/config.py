
DB_HOST = _setting("DB_host", "localhost")
DB_PORT     = int(_setting("DB_port", 3306))
DB_NAME     = _setting("DB_name", "metro_laptop")
DB_USER     = _setting("DB_username")
DB_PASSWORD = _setting("DB_password")
DB_SSL_CA   = _setting("DB_ssl_ca", None)        # path to ca.pem
DB_SSL_VERIFY = _as_bool(_setting("DB_ssl_verify_cert", False))
DB_TIMEOUT  = int(_setting("DB_timeout", 30))
DB_TABLE    = _setting("DB_table", "laptop_dataset")