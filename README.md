 SenzingGo

## Overview

The SenzingGo utility provides rapid deployment of the following Docker containers on a bare metal Linux installation of the Senzing APIs:
- [Senzing REST API Server](https://github.com/Senzing/senzing-api-server)
- [Senzing Entity Search App (sample demo application)](https://github.com/Senzing/entity-search-web-app)
- [Swagger UI](https://swagger.io/tools/swagger-ui/)

SenzingGo is intended to be easy to use and deploy resources quickly to aid in getting started with the Senzing APIs; without requiring Docker skills. Due to its rapid deployment and ease of use, it is targetted at testing, development and education. 

SenzingGo is not intended for production use, it does not provide authentication or secure transport of communications. Such topics are outside the intended use and scope of SenzingGo.

### Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Usage Overview](#usage-overview)
4. [Usage](#usage)
5. [Options](#options)
	1. [Specifying Ports](#specifying-ports)
	1. [Starting Specific Containers](#starting-specific-containers)
	1. [Cleaning Up Containers](#cleaning-up-containers)
	1. [Information and Logs](#information-and-logs)
	1. [Packaging and Deploying the Docker Images](#packaging-and-deploying-the-docker-images)
	1. [Starting REST Server in Admin Mode](#starting-rest-server-in-admin-mode)

### Legend
1. :thinking: - A "thinker" icon means that a little extra thinking may be required.
   Perhaps you'll need to make some choices.
   Perhaps it's an optional step.
1. :pencil2: - A "pencil" icon means that the instructions may need modification before performing.
1. :warning: - A "warning" icon means that something tricky is happening, so pay attention.

### Prerequisites

- [Supported Linux operating system](https://senzing.zendesk.com/hc/en-us/articles/115010259947)
- [Senzing APIs installation](https://senzing.zendesk.com/hc/en-us/articles/115001579954-API-Quickstart-Roadmap)
- Creation of a Senzing project (see above link)
- [Docker](https://docs.docker.com/engine/install/)
- Internet access (for initial pull of Docker images)
- Python Docker module

    ```console
    pip3 install docker
    ```
- sudo access or user added to the Linux docker group
  - SenzingGo executes API calls against Docker and [privileges](https://docs.docker.com/engine/install/linux-postinstall/) to use it are required

:warning: Recent versions of Red Hat systems use Podman in place of Docker. Podman is not currently supported, see the Docker link above for installation of Docker if you don't rely on Podman.

:warning: MS SQL Server is currently not supported as a Senzing repository when using SenzingGo, please contact [support](https://senzing.zendesk.com/hc/en-us/requests/new) if this is a requirement. 

### Installation

SenzingGo will be included in V3 of the Senzing APIs. In the meantime:
1. Download SenzingGo.py and place it in the python directory of your Senzing API project
2. Add execute permission to SenzingGo.py
    ```console
    cd <project_path>/python
    chmod +x SenzingGo.py
    ```

4. As usual, ensure you have sourced the setupEnv file for your Senzing API project to set the Senzing environment

    ```console
    source <project_path>/setupEnv
    ```

### Usage Overview

```console
 usage: SenzingGo.py [-h] [-c INIFILE] [-ap PORT] [-wp PORT] [-sp PORT] [-nwa] [-nsw] [-s | -r | -rn] [-i] [-l [STRING]] [-si [IMAGE [IMAGE ...]]] [-sip PATH] [-li FILE] [-aa] [-n [NAME]] [-ho [HOST]]
                    [-ps SUFFIX] [-db2c DB2CLIPATH]

Utility to rapidly deploy Docker containers for REST API server, Entity Search App and Swagger UI

Additional information: https://github.com/Senzing/senzinggo

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
                        
  -s, --contStop        Stop any Docker containers named *2_8_3-Release
                        
  -r, --contRemove      Stop and remove any Docker containers named *2_8_3-Release
                        
  -rn, --contRemoveNoPrompt
                        Stop and remove any Docker containers named *2_8_3-Release without prompting
                        
  -i, --info            Display info for running containers for this project
                        
  -l [STRING], --logs [STRING]
                        Display logs for running container(s), use partial string to match multiple containers, default=SzGo
                        
  -si [IMAGE [IMAGE ...]], --saveImages [IMAGE [IMAGE ...]]
                        Save SenzingGo Docker images for loading on another machine, e.g. air gapped systems
                        
                        Unless instructed by Senzing support no arguments are required.
                        
  -sip PATH, --saveImagesPath PATH
                        Path for saving a Docker images package to, default=/home/ant/senzprojs/2_8_3-Release/var
                        
  -li FILE, --loadImages FILE
                        File to load SenzingGo Docker images from to this machine, e.g. air gapped systems
                        
  -aa, --apiAdmin       Enable admin mode on the API Server
                        
  -n [NAME], --dockNet [NAME]
                        Name of a Docker network to create or use, default=szgo-network
                        
  -ho [HOST], --host [HOST]
                        Hostname or IP address, only use if tool can't determine correctly, default=ant76
                        
  -ps SUFFIX, --projectSuffix SUFFIX
                        Suffix to use for container names, default=2_8_3-Release
                        
  -db2c DB2CLIPATH, --db2CliPath DB2CLIPATH
                        Path to Db2 client CLI driver when using a Db2 database as the Senzing repository

```

### Usage

Although SenzingGo has many arguments, it is executed in its simplest form with no arguments. 

```
./SenzingGo.py
```

Upon execution the script will:

1. Perform checks to ensure Docker is installed and the current user has privileges to execute Docker commands
2. Check for the latest versions of Docker images utilized
3. Pull the required Docker images (if not already locally available)
4. Run the Docker images and instantiate running containers for the previously described assets
5. Print URL information for each of the services provided by the Docker containers

```
-> ./SenzingGo.py 

Performing Docker checks...

Docker network szgo-network doesn't exist, creating...

Looking for existing containers to remove...

Checking for internet access and Senzing resources...

	https://raw.githubusercontent.com/Senzing/knowledge-base/master/lists/docker-versions-latest.sh Available
	https://hub.docker.com/u/senzing/ Available


Checking and pulling Docker images, this may take many minutes...


	Pulling senzing/senzing-api-server:2.7.5...

	Pulling senzing/entity-search-web-app:2.3.3...

	Pulling swaggerapi/swagger-ui:v3.52.4...

Running senzing/senzing-api-server:2.7.5...

	Waiting for container to start.
	Waiting for container to become healthy.......

	Fetching API specification from REST server

Running senzing/entity-search-web-app:2.3.3...

	Waiting for container to start.
	This container doesn't report health
	Use the command "docker logs SzGo-WEB-2_8_3-Release" to check status if issues arise 

Running swaggerapi/swagger-ui:v3.52.4...

	Waiting for container to start.
	This container doesn't report health
	Use the command "docker logs SzGo-Swagger-2_8_3-Release" to check status if issues arise 


Resources
---------

REST API Server: http://ant76.anthome:8250
Web App demo:    http://ant76.anthome:8251
Swagger GUI:     http://ant76.anthome:9180

Help: https://github.com/Senzing/senzinggo

~/senzprojs/2_8_3-Release/python 
->
```

Once complete, access to each of the services is available at the URL and port detailed at the end of the output. For example, in the above output the Senzing demo entity search application is accessible from a browser at http://ant76.anthome:8251.

SenzingGo is designed to be run from within a previously created Senzing project. This facilitates having multiple projects (dev, test, stage or different versions of the Senzing APIs) and distinct containers for the above services serving a single project. A consideration for running multiple projects and instances of the containers started by SenzingGo is specifying different ports than those used by default. See [Specifying Ports](#specifying-ports)

![Multiple Projects](/docs/img/MultiInstance.png)

Upon startup, and if an internet connection is available, SenzingGo will check for the latest version of the Docker images and attempt to pull them for use. Although an internet connection is usually expected by SenzingGo, and is initially required to pull the Docker images it uses, SenzingGo can work in an 'offline' mode. When offline and an internet connection isn't available, SenzingGo will check the locally available Docker images to determine if the images it needs to start are available. This allows SenzingGo to continue to operate without an internet connection.

There is another use case where it is useful for SeningGo to be able to run offline: air gapped systems. In this use case SenzingGo can be used on an internet connected machine to package the required Docker images together. This package can be moved to an air gapped system where SenzingGo can deploy the Docker images for use without needing to pull them directly from the internet, see [Packaging and Deploying the Docker Images](#packaging-and-deploying-the-docker-images)

### Options

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
- ```--contRemoveNoPrompt```
	- Stop any containers for the currently active Senzing project, and remove the containers without prompting

#### Information and Logs

Upon completion of execution, SenzingGo displays information relating to the URL and port for each service. If this information is lost sight of from the terminal it can be recalled again by using the ```--info``` option. The info option displays the URL and port information along with other pertinent information for the running containers.

```--> ./SenzingGo.py --info

Performing Docker checks...


Looking for containers matching 2_8_3-Release...

Container: SzGo-Swagger-2_8_3-Release

	Image:  swaggerapi/swagger-ui:v3.52.4
	Status: running
	URL:    http://ant76.anthome:9180

Container: SzGo-WEB-2_8_3-Release

	Image:  senzing/entity-search-web-app:2.3.3
	Status: running
	URL:    http://ant76.anthome:8251

Container: SzGo-API-2_8_3-Release

	Image:  senzing/senzing-api-server:2.7.5
	Status: running
	URL:    http://ant76.anthome:8250


Command the REST API Server container is starting with:

    --enable-admin false --allowed-origins * --concurrency 10 --read-only false --verbose true --http-port 8250 --bind-addr all --init-file /etc/opt/senzing/G2Module.ini_SzGo.json
```

The ```--logs``` option is used to display each of the logs for currently running containers started by SenzingGo. This can be useful in helping determine problems with starting the containers and will be of use to Senzing support:

```./SenzingGo.py --logs```

#### Packaging and Deploying the Docker Images

In situations where the Senzing APIs are being utilized on systems with no internet connection, and there is a requirement to use SenzingGo, SenzingGo can be used on an internet connected machine to package the required Docker images for deployment on the non-internet connected machine. This is typically useful in environments that have air gapped systems. The sequence of events in such a situation would be:

1. On the internet connected machine ensure the Prerequisites are met 
	1. :thinking: Installation of the Senzing APIs and creation of a project is not required. SenzingGo can be run standalone when using ```--saveImages``` or ```--loadImages```


2. Run SenzingGo with the ```--saveImages``` option
	1. No arguments are required to ```--saveImages```

```
--> ./SenzingGo.py --saveImages

WARNING: SENZING_ROOT isn't set please source the project setupEnv file to use all features

WARNING: Without SENZING_ROOT set, only --saveImages (-si) and --loadImages modes are available

Performing Docker checks...

Checking for internet access and Senzing resources...

	https://raw.githubusercontent.com/Senzing/knowledge-base/master/lists/docker-versions-latest.sh Available
	https://hub.docker.com/u/senzing/ Available


Checking and pulling Docker images, this may take many minutes...


	Pulling senzing/senzing-api-server:2.7.5...

	Pulling senzing/entity-search-web-app:2.3.3...

	Pulling swaggerapi/swagger-ui:v3.52.4...

Saving senzing/entity-search-web-app:2.3.3 to /tmp/SzGoPackage-senzing-entity-search-web-app-2.3.3.tar...

Saving senzing/senzing-api-server:2.7.5 to /tmp/SzGoPackage-senzing-senzing-api-server-2.7.5.tar...

Saving swaggerapi/swagger-ui:v3.52.4 to /tmp/SzGoPackage-swaggerapi-swagger-ui-v3.52.4.tar...

Compressing saved images to /tmp/SzGoImages_20211122_155051.tgz, this will take several minutes...

Move /tmp/SzGoImages_20211122_155051.tgz to the system to load the images to and run this tool with --loadImages (-li)
```

3. Move the created package to the non-internet connected machine
	1. :thinking: If you don't have the Senzing API installation package or SenzingGo.py on the target machine already now would be a good time to move them also 

4. Run SenzingGo with the ```--loadImages``` option, specifying the name of the package, on the non-internet connected machine

```
--> ./SenzingGo.py --loadImages /tmp/SzGoImages_20211122_155051.tgz

WARNING: SENZING_ROOT isn't set please source the project setupEnv file to use all features

WARNING: Without SENZING_ROOT set, only --saveImages (-si) and --loadImages modes are available

Performing Docker checks...

Extracting Senzing Docker images from /tmp/SzGoImages_20211122_155051.tgz...
	Loading image file SzGoPackage-senzing-entity-search-web-app-2.3.3.tar
	Loading image file SzGoPackage-senzing-senzing-api-server-2.7.5.tar
	Loading image file SzGoPackage-swaggerapi-swagger-ui-v3.52.4.tar
```

At this point the 3 required Docker images should be available on the local machine. Assuming the Senzing APIs have been installed, a Senzing project created and SenzingGo.py is available, SenzingGo will detect there is no internet connection but the required images are available to use as normal.

:thinking: Anytime one of the Docker images is updated and the update required on the non-internet connected machine the same process can be repeated to update the images.

When saving the images, a default location will be used (either /tmp or <project_path>/var/), to specify the location to save the package to use the ```--saveImagesPath``` option.

```./SenzingGo.py --saveImages --saveImagesPath /home/ant```


#### Starting REST Server in Admin Mode

To enable additional functionality in the Senzing REST API Server and Entity Search App the REST Server needs to be started in admin mode. The additional functionality includes making config changes via the REST Server and loading data from the Entity Search App. To start the REST server in admin mode:

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

When using the ```--projectSuffix``` be aware it is required to be used with other command options. For example, to remove the 3 containers with the ```--contRemoveNoPrompt``` option, the ```--projectSuffix``` option must also be used to specify the suffix:

```
--> ./SenzingGo.py -rn --projectSuffix My_Sample_Demo

Performing Docker checks...

Looking for existing containers to remove...

	SzGo-Swagger-My_Sample_Demo
		Stopping...
		Removing...

	SzGo-WEB-My_Sample_Demo
		Stopping...
		Removing...

	SzGo-API-My_Sample_Demo
		Stopping...
		Removing...


Removing Docker network szgo-network
```









