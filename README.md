# Installation
Requirements
  - Vault
  - Docker
  - VaultAIDE code
  - Slack workspace with space for a new app
  - Nginx
  - In case you want TLS on your http Interface you need a valid certificate SSL (not self-signed)

  If you don’t have Vault Or Docker installed follow these instructions instead go to Install VaultAIDE

## Install Docker
  Go to https://docs.docker.com/get-docker/ and follow the steps for your distribution  
  For Mac: https://docs.docker.com/docker-for-mac/install/  
  For Windows: https://docs.docker.com/docker-for-windows/install/  
  For Linux: https://docs.docker.com/engine/install/  

## Install Vault
  Go to https://www.vaultproject.io/downloads and select the button for your operating system and architecture  
  Then go to https://learn.hashicorp.com/vault/getting-started/install to learn how to install the package  
  When you’re done you need to go to a terminal and execute this commands:  
  ```bash
  vault operator init
  ```
  You will see 5 unseal keys and one initial root token  
  Now follow the instructions https://www.vaultproject.io/docs/commands/operator/unseal with 3 of 5 keys  
  
  Once you unseal vault need to run
  ```bash
  vault audit enable socket address=web:9090 socket_type=tcp
  ```

  This one is to enable the socket that our bot will be using  
  After that you can use your Vault normally and start to experiment with it  
  
  ## Install VaultAIDE
  Clone this repo and run
  ```bash
  docker-compose up --build
  ```
  
  ## Slack configuration
  We need to create an app in slack  
  Go to https://api.slack.com/apps  
  - Click Create new app  
  - Name your app as VaultAide or whatever you want  
  - After your app is created go to the Left side **Menu -> Features -> OAuth & Permissions**  
  - Go down to **Scopes** and select this for bot token scopes:
  <img width="647" alt="Screen Shot 2020-08-27 at 17 38 12" src="https://user-images.githubusercontent.com/51725996/91501830-1beffe80-e88c-11ea-94bd-b1bd93de13fd.png">
  
  and this for user token scopes:  
  <img width="633" alt="Screen Shot 2020-08-27 at 17 39 02" src="https://user-images.githubusercontent.com/51725996/91501873-37f3a000-e88c-11ea-8780-838a3d7f1136.png">
  
  Then on top of the page click Install your app
  - Copy the “Bot User OAuth Access Token” and make sure to save that token because later we are going to need it.
  - Go to the Left side Menu -> Event Subscriptions
  - Click the toggle button to turn it on
  - A field text will appear.  
  For this you need to expose your app in some domain. We recommend to use [ngrok](https://ngrok.com/) 
  - Add domain URL + slack/get-answer    
  Example: My url is https://8cd73700.ngrok.io so in my Request URL I’m going to write https://8cd73700.ngrok.io/slack/get-answer (This is the way slack will be sending notifications to our VaultAide to get Vault information)  
  After you get a Verified text in your URL go down and click Subscribe to bot events and select this ones:  
  <img width="617" alt="Screen Shot 2020-08-27 at 17 52 41" src="https://user-images.githubusercontent.com/51725996/91502616-1eebee80-e88e-11ea-844f-c2d08e68c50d.png">  
  
  - Now click **Subscribe** to events on behalf of users and select this events:  
  <img width="626" alt="Screen Shot 2020-08-27 at 17 53 24" src="https://user-images.githubusercontent.com/51725996/91502675-46db5200-e88e-11ea-869c-9955729d5407.png">  
  
  - Then click Save Changes in some cases a message for reinstall your app may appear. You just need to click the text that says Reinstall your app
  - Go to your workspace in slack and create a channel, you can name this as you like.
  
  ## Vault Token
  For develop purposes you can use the root token of your vault instance.
  
  ## VaultAIDE configuration
  In a browser like Chrome, go to your domain URL + / config.  
  Example: My domain as you know is https://8cd73700.ngrok.io so in my browser I’m going to write https://8cd73700.ngrok.io/config

  It is time to give the information to our application.   
  In this page you are going to save  
  - Slack token
  - Vault token
  - Slack channel
  - Address for:
    - Vault 
    - Audit Device 
    - HTTP Interface   
    
  You will see a Notifications section
  Those are the available notifications that this app can provide so you can select what are useful for your purposes
  - [x] Version Updates will check your vault version and compare with the latest available so in case you don’t have the latest this app will let you know
  - [x] Adoption Stats will give you some general information about your Vault
  - [x] Extant Leases will deliver information about the leases like the total leases
  - [x] Lease Optimization will check if you are giving to many ttl to your leases and suggest some changes about it
  - [x] Admin Access Alert will deliver a notification every time that an admin token perform an action in your vault
  - [x] Admin Creation Alert will deliver a notification every time that a root account is created in your Vault.
  - [x] Unused resources will check if you have some secrets engine that you are  not using
  - [x] Intrusion Detection will be watching the unwrapping action so the app can let you know when some unwrapping failure is detected
  - [x] Vault Posture Score will be checking some points to let you know how close you are to being "as secure as possible"
  - [x] Auth Method Suggestions will check if you are using secure auth methods and if you’re not then will suggest some upgrades  
    
  After you populate all the information you can click Save
  Our application will restart and we can wait just for the first notification to appear.
  
  ## Usage
  Type in the slack channel some of this:
  - Adoption Stats
  - Vault Score
  - Version
  - Lease Optimization

  ## Vault Resources
  - Version Updates:  
  HTTP request to ***/v1/sys/health*** to get the version value (GET)
  - Extant Leases:  
  HTTP request to ***/v1/sys/leases/lookup/auth/token/*** create to get the total leases (LIST)
  - Adoption Stats:  
  Audit Log entries to get number of operations per month or week
  Python client HVAC -> List of auth methods, secrets engine, policies
  HTTP request to ***/v1/identity/entity/id*** to get the total entities (LIST)
  HTTP request to ***/v1/auth/token/accessors*** to get total tokens (LIST)
  HTTP request to ***/sys/auth/roles*** and ***/sys/auth/users*** to get total roles (LIST)
  - Lease Optimization:  
  Audit Log entries to get the ttl and time of use for every lease
  - Admin Access Alert:  
  Audit Log entries to know when a root token is used
  - Admin Creation Alert:  
  Audit Log entries to know when a root token is created
  - Unused Resources:  
  Audit Log entries to get resources with no log entries
  - Intrusion Detection:  
  Audit Log entries to track unwrapping token fails
  - Vault Posture Score:  
  We use some of the previous functions like 
  Version Updates
  Admin Access and Creation Alert
  Python CLient HVAC -> List of Auth methods

