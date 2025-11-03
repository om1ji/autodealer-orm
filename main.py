from firebird.driver import connect

# Attach to 'employee' database/alias using embedded server connection
con = connect('employee', user='sysdba', password='masterkey')

# Attach to 'employee' database/alias using local server connection
from firebird.driver import driver_config
driver_config.server_defaults.host.value = 'localhost'
con = connect('employee', user='sysdba', password='masterkey')

# Set 'user' and 'password' via configuration
driver_config.server_defaults.user.value = 'SYSDBA'
driver_config.server_defaults.password.value = 'masterkey'
con = connect('employee')