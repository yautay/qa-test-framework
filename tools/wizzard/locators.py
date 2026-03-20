CONTAINER_test = "//div[@id='headingtestnetcornerpl']/parent::div"
CONTAINER_alfa = "//div[@id='headingalfanetcornerpl']/parent::div"
CONTAINER_gamma = "//div[@id='headinggammanetcornerpl']/parent::div"
CONTAINER_zeta = "//div[@id='headingzetanetcornerpl']/parent::div"
CONTAINERS_all = (
    "//div[@id='headingtestnetcornerpl' or @id='headingalfanetcornerpl' "
    "or @id='headinggammanetcornerpl' or @id='headingzetanetcornerpl']/parent::div"
)
CONTAINERS_test_and_alfa = "//div[@id='headingtestnetcornerpl' or @id='headingalfanetcornerpl']/parent::div"
ELEMENTS_vms_details = "//table[contains(@class, 'vm-list')]/tbody/tr[contains(@id, 'details')]"
ELEMENTS_vms_ssh_containers = "//span[contains(., 'SSH Netcorner')]/ancestor::tr"
INPUTS_vms_nc_ssh = "//input[contains(@id, 'nc-connection') and contains (@value, 'ssh')]"

ELEMENTS_test_vms = "//div[@class='fl']/div[1]"
ELEMENTS_test_owners = "//div[@id='vm-{vm}-creator']"
