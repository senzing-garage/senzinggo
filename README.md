 # SenzingGo

 If you are beginning your journey with
[Senzing](https://senzing.com/),
please start with
[Senzing Quick Start guides](https://docs.senzing.com/quickstart/).

You are in the
[Senzing Garage](https://github.com/senzing-garage)
where projects are "tinkered" on.
Although this GitHub repository may help you understand an approach to using Senzing,
it's not considered to be "production ready" and is not considered to be part of the Senzing product.
Heck, it may not even be appropriate for your application of Senzing!

## QuickStart

SenzingGo is included in a bare metal install from V3. Follow the [Senzing Quickstart](https://senzing.zendesk.com/hc/en-us/articles/115001579954-API-Quickstart-Roadmap), from the same shell within the project directory:

```
python3 -m pip install docker
./python/SenzingGo.py
```

## Overview

The SenzingGo utility provides rapid deployment of the following Docker containers on a bare metal Linux installation of the Senzing APIs:
- [Senzing REST API Server](https://github.com/senzing-garage/senzing-api-server)
- [Senzing Entity Search App (sample demo application)](https://github.com/senzing-garage/entity-search-web-app)
- [Swagger UI](https://swagger.io/tools/swagger-ui/)

SenzingGo is intended to be easy to use and deploy resources quickly to aid in getting started with the Senzing APIs; without requiring Docker skills. Due to its rapid deployment and ease of use, it is targeted at testing, development and education. 

SenzingGo is not intended for production use, it does not provide authentication or secure transport of communications. Such topics are outside the intended scope of SenzingGo.

### Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Usage Overview](#usage-overview)
4. [Usage](#usage)
5. [Options](#options)
	1. [Docker Networking](#docker-networking)
	1. [Specifying Ports](#specifying-ports)
	1. [Starting Specific Containers](#starting-specific-containers)
	1. [Cleaning Up Containers](#cleaning-up-containers)
	1. [Information and Logs](#information-and-logs)
	1. [Packaging and Deploying the Docker Images](#packaging-and-deploying-the-docker-images)
	1. [Starting REST Server in Admin Mode](#starting-rest-server-in-admin-mode)
	1. [Change Container Name Suffix](#change-container-name-suffix)
	1. [Db2 CLI Drivers Path](#db2-cli-drivers-path)

### Legend
1. :thinking: - A "thinker" icon means that a little extra thinking may be required.
   Perhaps you'll need to make some choices.
   Perhaps it's an optional step.
1. :pencil2: - A "pencil" icon means that the instructions may need modification before performing.
1. :warning: - A "warning" icon means that something tricky is happening, so pay attention.

### Prerequisites

- [Supported Linux operating system](https://senzing.zendesk.com/hc/en-us/articles/115010259947)
- [Senzing APIs installation and project creation](https://senzing.zendesk.com/hc/en-us/articles/115001579954-API-Quickstart-Roadmap)
- [Docker](https://docs.docker.com/engine/install/)
- Internet access (for initial pull of Docker images)
- Python Docker module

    ```console
    pip3 install docker
    ```
- sudo access or user added to the Linux docker group
  - SenzingGo executes API calls against Docker and [privileges](https://docs.docker.com/engine/install/linux-postinstall/) to use it are required

:warning: Recent versions of Red Hat systems use Podman in place of Docker. Podman is not currently supported, see the Docker link above for installation of Docker if you don't rely on Podman.

:warning: MS SQL Server and Oracle are currently not supported as a Senzing repository when using SenzingGo, please contact [support](https://senzing.zendesk.com/hc/en-us/requests/new) if this is a requirement. 

### Installation

SenzingGo is included in V3+ of the Senzing APIs.

### Usage Overview

```console
usage: SenzingGo.py [-h] [-c INIFILE] [-ap PORT] [-wp PORT] [-sp PORT] [-nwa] [-nsw] [-s | -r] [-i] [-l [STRING]] [-si [IMAGE [IMAGE ...]]] [-sip PATH] [-li FILE] [-aa] [-n [NAME]]
                    [-du URL] [-ho [HOST]] [-ps SUFFIX] [-db2c DB2CLIPATH] [-wh] [-u]

Utility to rapidly deploy Docker containers for REST API server, Entity Search App and Swagger UI

Additional information: https://github.com/senzing-garage/senzinggo

optional arguments:
  -h, --help            show this help message and exit
  -c INIFILE, --iniFile INIFILE
                        Path and file name of optional G2Module.ini to use.
                        
  -ap PORT, --apiHostPort PORT
                        Port number of the REST API server, default=8250
                        
  -wp PORT, --webAppHostPort PORT
                        Port number of the Search Web App demo, default=8251
                        
  -sp PORT, --swaggerHostPort PORT
                        Port number of Swagger UI, default=9180
                        
  -nwa, --noWebApp      Don't deploy the Search Web App demo
                        
  -nsw, --noSwagger     Don't deploy the Swagger UI
                        
  -s, --contStop        Stop any Docker containers named *3_2_0_22234
                        
  -r, --contRemove      Stop and remove any Docker containers named *3_2_0_22234
                        
  -i, --info            Display info for running containers for this project
                        
  -l [STRING], --logs [STRING]
                        Display logs for running container(s), use partial string to match multiple containers, default=SzGo
                        
  -si [IMAGE [IMAGE ...]], --saveImages [IMAGE [IMAGE ...]]
                        Save SenzingGo Docker images for loading on another machine, e.g. air gapped systems
                        
                        Unless instructed by Senzing support no arguments are required.
                        
  -sip PATH, --saveImagesPath PATH
                        Path for saving a Docker images package to, default=/home/ant/senzprojs/3.2.0.22234/var
                        
  -li FILE, --loadImages FILE
                        File to load SenzingGo Docker images from to this machine, e.g. air gapped systems
                        
  -aa, --apiAdmin       Enable admin mode on the API Server
                        
  -n [NAME], --dockNet [NAME]
                        Name of a Docker network to create or use, default=szgo-network
                        
  -du URL, --dockUrl URL
                        URL for Docker server, default=unix://var/run/docker.sock
                        
  -ho [HOST], --host [HOST]
                        Hostname, only use if tool can't determine correctly
                        
  -ps SUFFIX, --projectSuffix SUFFIX
                        Suffix to use for container names, default=3_2_0_22234
                        
  -db2c DB2CLIPATH, --db2CliPath DB2CLIPATH
                        Path to Db2 client CLI driver when using a Db2 database as the Senzing repository
                        
  -wh, --waitHealth     Wait for health checking on containers starting, use if errors are reported during a run
                        
  -u, --update          Update check

```

### Usage

Although SenzingGo has many arguments, it is executed in its simplest form with no arguments. 

```
./SenzingGo.py
```

Upon execution the script will:

1. Perform checks to ensure Docker is installed and the current user has privileges to execute Docker commands
2. Check for the latest versions of Docker images utilized
3. Check if there are updates to SenzingGo
3. Pull the required Docker images (if not already locally available)
4. Run the Docker images and instantiate running containers for the previously described assets
5. Print URL information for each of the services provided by the Docker containers

![SenzingGo Run](/docs/img/SenzingGoRun.png)

Once complete, access to each of the services is available at the URL and port detailed at the end of the output. For example, in the above output the Senzing demo entity search application is accessible from a browser at http://ant76.anthome:8251.

SenzingGo is designed to be run from within a previously created Senzing project. This facilitates having multiple projects (dev, test, stage or different versions of the Senzing APIs) and distinct containers for the above services serving a single project. A consideration for running multiple projects and instances of the containers started by SenzingGo is specifying different ports than those used by default. See [Specifying Ports](#specifying-ports)

![Multiple Projects](/docs/img/MultiInstance.png)

Upon startup, and if an internet connection is available, SenzingGo will check for the latest version of the Docker images and attempt to pull them for use. Although an internet connection is usually expected by SenzingGo, and is initially required to pull the Docker images it uses, SenzingGo can work in an 'offline' mode. When offline and an internet connection isn't available, SenzingGo will check the locally available Docker images to determine if the images it needs to start are available. This allows SenzingGo to continue to operate without an internet connection.

There is another use case where it is useful for SeningGo to be able to run offline: air gaped systems. In this use case SenzingGo can be used on an internet connected machine to package the required Docker images together. This package can be moved to an air gapped system where SenzingGo can deploy the Docker images for use without needing to pull them directly from the internet, see [Packaging and Deploying the Docker Images](#packaging-and-deploying-the-docker-images)

### Options

#### Docker Networking

If you have set ```"userland-proxy": false``` in your Docker configuration file (/etc/docker/daemon.json) and your Senzing database is also using a Docker container, SenzingGo will fail with connection issues. SenzingGo uses a network (the deafult is szgo-network) for the containers it starts. Your database container will not be using the same network. 

To start the database container in the default SenzingGo network:
```console
docker run --net szgo-network ...
```

The other option is if your database container is specifying a Docker network to use, instruct SenzingGo to use that network instead: 
```console
./SenzingGo.py -n <netwrok_name>
```

Note, the containers cannot use the default Docker bridge network or they cannot discover each other by service name; this is by design for this network.

#### Specifying Ports

Each of the three services will use default ports - 8250, 8251 and 9180 - there are a couple of cases where you may need to specify different port numbers:

1. The ports 8250, 8251 or 9180 are already in use on the system
2. There are multiple Senzing API projects on a single system and SenzingGo is to be used with each

In the instance a port is already in use, the following error message (or similar) is displayed and SenzingGo cannot continue.

```
ERROR: 500 Server Error for http+docker://localhost/v1.41/containers/0e229d2fbf4676a2d8dc5ded8a00dc3c75a7cb44fc189dcf9e43a3aba576a94b/start: Internal Server Error ("driver failed programming external connectivity on endpoint SzGo-API-2_7_0-Release (37b781741cc80ff1bc45c02646272443f91b54171c58890e2814dafb21c444a4): Bind for 0.0.0.0:8250 failed: port is already allocated")
```

To launch SenzingGo and use alternative port numbers, specify one or more of:

```
./SenzingGo.py --apiHostPort 8252 --webAppHostPort 8253 --swaggerHostPort 9181
```

#### Starting Specific Containers

Running SenzingGo without any parms will start all three of the default containers: Senzing REST API Server, Senzing Entity Search App and the Swagger UI. There may be situations where you don't intend to use all 3 and don't wish to use resources starting them. To choose not to start either the Senzing Entity Search App or the Swagger UI the ```--noWebApp``` and ```--noSwagger``` options can be used. Note: the REST API Server always starts and is the minimum requirement.

Start the Senzing REST API Server and the Senzing Entity Search App:

```./SenzingGo.py --noSwagger```

Start only the Senzing REST API Server:

```./SenzingGo.py --noWebApp --noSwagger```

#### Cleaning up Containers

When you no longer require the use of any of the services provided by the containers, you can stop and/or clean up the containers:

- ```--contStop```
	- Stop any containers for the currently active Senzing project 
- ```--contRemove```
	- Stop any containers for the currently active Senzing project, and remove the containers

#### Information and Logs

Upon completion of execution, SenzingGo displays information relating to the URL and port for each service. If this information is lost sight of from the terminal it can be recalled again by using the ```--info``` option. The info option displays the URL and port information along with other pertinent information for the running containers.
  
![SenzingGo Info](/docs/img/SenzingGoInfo.png)

The ```--logs``` option is used to display each of the logs for currently running containers started by SenzingGo. This can be useful in helping determine problems with starting the containers and will be of use to Senzing support:

```./SenzingGo.py --logs```

#### Packaging and Deploying the Docker Images

In situations where the Senzing APIs are being utilized on systems with no internet connection, and there is a requirement to use SenzingGo, SenzingGo can be used on an internet connected machine to package the required Docker images for deployment on the non-internet connected machine. This is typically useful in environments that have air gapped systems. The sequence of events in such a situation would be:

1. On the internet connected machine ensure the Prerequisites are met 
	1. :thinking: Installation of the Senzing APIs and creation of a project is not required. SenzingGo can be run standalone when using ```--saveImages``` or ```--loadImages```


2. Run SenzingGo with the ```--saveImages``` option
	1. No arguments are required to ```--saveImages```

![Save Images](/docs/img/SaveImages.png)

3. Move the created package to the non-internet connected machine
	1. :thinking: If you don't have the Senzing API installation package or SenzingGo.py on the target machine already, transfer them to the target machine now 

4. Run SenzingGo with the ```--loadImages``` option, specifying the name of the package, on the non-internet connected machine

![Load Images](/docs/img/LoadImages.png)

At this point the 3 required Docker images should be available on the local machine. Assuming the Senzing APIs have been installed, a Senzing project created and SenzingGo.py is available, SenzingGo will detect there is no internet connection but the required images are available to use as normal.

:thinking: Anytime one of the Docker images is updated and the update required on the non-internet connected machine the same process can be repeated to update the images.

When saving the images, a default location will be used (either /tmp or <project_path>/var/), to specify the location to save the package to use the ```--saveImagesPath``` option.

```./SenzingGo.py --saveImages --saveImagesPath /home/ant```


#### Starting REST Server in Admin Mode

To enable additional functionality in the Senzing REST API Server and Entity Search App the REST Server needs to be started in admin mode. The additional functionality includes making configuration changes via the REST Server and loading data from the Entity Search App. To start the REST server in admin mode:

```./SenzingGo.py --apiAdmin```

#### Change Container Name Suffix

By default, SenzingGo will use the name of the project as a suffix when creating the container names to distinguish from containers used by other projects. In the following Docker output note the name of each of the containers created by SenzingGo have the suffix '2_8_3-Release', this is the name of the active Senzing project. 

```
--> docker ps -a --format "{{.ID}}    {{.State}}    {{.Names}}"
10308ec5b7a6    running    SzGo-Swagger-2_8_3-Release
f24ce403b526    running    SzGo-WEB-2_8_3-Release
2012006ef60b    running    SzGo-API-2_8_3-Release
```

Using the project name helps to identify the containers used by a project. If however, you wanted to use a different suffix the ```--projectSuffix``` option can be used:

```
./SenzingGo.py --projectSuffix My_Sample_Demo
```

Note the new suffix:

```
--> docker ps -a --format "{{.ID}}    {{.State}}    {{.Names}}"
9a12e9d225a9    running    SzGo-Swagger-My_Sample_Demo
60de596a90b4    running    SzGo-WEB-My_Sample_Demo
3030d07b2652    running    SzGo-API-My_Sample_Demo
```

When using ```--projectSuffix```, be aware it is required to be used with other command options. For example, to remove the 3 containers with the ```--contRemove``` option, the ```--projectSuffix``` option must also be used to specify the suffix.


#### Db2 CLI Drivers Path

When using Db2 as the Senzing repository you will have already installed the Db2 CLI client and drivers. To mount the drivers into the REST API container for use, SenzingGo must be informed of the location of these drivers on the host system. The path specified for this option should be the location of the Db2 client CLI drivers where the directories such as /cfg and /lib are located, for example /opt/IBM/db2_cli_odbc_driver/odbc_cli/clidriver
                        
```./SenzingGo.py --db2CliPath /opt/IBM/db2_cli_odbc_driver/odbc_cli/clidriver```
