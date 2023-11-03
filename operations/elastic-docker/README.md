# Elastic


# requirements

    docker and docker-compose
    openSSL

[installing docker on windows](https://docs.docker.com/desktop/install/windows-install/)

[install docker on ubuntu](https://docs.docker.com/engine/install/ubuntu/)

# Install for development

Create and start the Elasticsearch and Kibana instance:

    docker-compose up -d

Open a browser and navigate to http://localhost:5601 to access Kibana.

Stop elastic

    docker-compose down

To delete all
    
    docker-compose down -v

# max virtual memory

[see fix on elastic docu](https://www.elastic.co/guide/en/elasticsearch/reference/current/docker.html#_set_vm_max_map_count_to_at_least_262144)

An error could occur: "Docker max virtual memory areas" to fix this you can increase the max virtual memory area with the follwoing command:

on windows 

To manually set it every time you reboot, you must run the following commands in a command prompt or PowerShell window every time you restart Docker:

    wsl -d docker-desktop -u root
    sysctl -w vm.max_map_count=262144

If you are on these versions of WSL and you do not want to have to run those commands every time you restart Docker, you can globally change every WSL distribution with this setting by modifying your %USERPROFILE%\.wslconfig as follows:

    [wsl2]
    kernelCommandLine = "sysctl.vm.max_map_count=262144"



on Linux (Fix not yet fully tested on linux)

1. Check the current value of vm.max_map_count by running the following command:
    
        sysctl vm.max_map_count

2. To temporarily increase the value, you can run the following command:

        sudo sysctl -w vm.max_map_count=262144

3. Verify that the value has been changed by running the sysctl command again:

        sysctl vm.max_map_count

4. If you want to make the change persistent across system reboots, you'll need to edit the system configuration file. The file location may vary depending on your Linux distribution, but the most common file is /etc/sysctl.conf. Open the file using a text editor with root privileges, such as sudo nano /etc/sysctl.conf, and add the following line:

        vm.max_map_count=262144

Save the file and exit the text editor.

5. To apply the changes from the configuration file without rebooting, run the following command:

        sudo sysctl -p
    
This will reload the system configuration and apply the new value for vm.max_map_count.