      

### <a id="documentation-body"></a>

![Hackolade image](static/image1.png?raw=true)

MongoDB Physical Model
----------------------

#### Schema for:

Model name: GrowthTrack

Author: Rashmi Singhal

Version: V1.0

Printed On: Tue Mar 01 2022 15:54:17 GMT+0530 (India Standard Time)

Created with: [Hackolade](https://hackolade.com/) - Polyglot data modeling for NoSQL databases, storage formats, REST APIs, and JSON in RDBMS

### <a id="contents"></a>

*   [Table of Contents](#contents)
*   [1\. Model](#model)
*   [2\. Databases](#containers)
    *   [2.1 Undefined Database](#no-bucket)
        
        [2.1.2. Collections](#no-bucket-children)
        
        [2.1.2.1 Client](#28ec4d90-97e6-11ec-9947-b7f0ab1a4e72)
        
        [2.1.2.2 Courses](#6fe13ff0-983e-11ec-a11a-61c866bfca96)
        
        [2.1.2.3 Credentials](#be6784d0-97db-11ec-9947-b7f0ab1a4e72)
        
        [2.1.2.4 Roles](#675aa9f0-97e6-11ec-9947-b7f0ab1a4e72)
        
        [2.1.2.5 Users](#7be6d480-97db-11ec-9947-b7f0ab1a4e72)
        
        [2.1.2.6 specializations](#01333ab0-9846-11ec-a11a-61c866bfca96)
        
        [2.1.2.7 studentApplicationForms](#86e576f0-9855-11ec-a11a-61c866bfca96)
        
        [2.1.2.8 studentSecondaryDetails](#d9a1d4b0-9850-11ec-a11a-61c866bfca96)
        
        [2.1.2.9 studentsPrimaryDetails](#64c55110-983e-11ec-a11a-61c866bfca96)
        
*   [3\. Relationships](#relationships)
    *   [3.1 New Relationship](#c9ce6320-984e-11ec-a11a-61c866bfca96)
    *   [3.2 New Relationship(1)](#c9da9820-984e-11ec-a11a-61c866bfca96)
    *   [3.3 fk Client. to Courses.](#94c3fb80-9845-11ec-a11a-61c866bfca96)
    *   [3.4 fk Client. to Users.](#43b90370-97eb-11ec-a19e-9d6e67c760cd)
    *   [3.5 fk Courses. to Students.](#3afc3142-984e-11ec-a11a-61c866bfca96)
    *   [3.6 fk Courses. to Students.](#3b0950a2-984e-11ec-a11a-61c866bfca96)
    *   [3.7 fk Courses. to specializations.](#20a35330-9846-11ec-a11a-61c866bfca96)
    *   [3.8 fk Courses. to studentApplicationForms.](#35badc20-98af-11ec-a8e6-f363f79d3ea0)
    *   [3.9 fk Roles. to Users.](#022c4480-97f5-11ec-8040-bdb9a5c9bfef)
    *   [3.10 fk Roles. to Users.](#1f3bd7c0-97f5-11ec-8040-bdb9a5c9bfef)
    *   [3.11 fk specializations. to studentApplicationForms.](#7bbdfc70-98af-11ec-a8e6-f363f79d3ea0)
    *   [3.12 fk specializations. to studentApplicationForms.](#8bf63530-98af-11ec-a8e6-f363f79d3ea0)
    *   [3.13 fk specializations. to studentApplicationForms.](#949a4640-98af-11ec-a8e6-f363f79d3ea0)
    *   [3.14 fk studentApplicationForms. to studentsPrimaryDetails.](#4362d7a0-98b0-11ec-a8e6-f363f79d3ea0)
    *   [3.15 fk studentsPrimaryDetails. to studentApplicationForms.](#333e4030-98ab-11ec-a8e6-f363f79d3ea0)
    *   [3.16 fk studentsPrimaryDetails. to studentSecondaryDetails.](#dfb77d40-9851-11ec-a11a-61c866bfca96)

### <a id="model"></a>

##### 1\. Model

##### 1.1 Model **GrowthTrack**

##### 1.1.1 **GrowthTrack** Entity Relationship Diagram

![Hackolade image](static/image2.png?raw=true)

##### 1.1.2 **GrowthTrack** Properties

##### 1.1.2.1 **Details** tab

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td><span>Model name</span></td><td>GrowthTrack</td></tr><tr><td><span>Technical name</span></td><td>GTM</td></tr><tr><td><span>Description</span></td><td><div class="docs-markdown"></div></td></tr><tr><td><span>Author</span></td><td></td></tr><tr><td><span>Version</span></td><td></td></tr><tr><td><span>DB vendor</span></td><td>MongoDB</td></tr><tr><td><span>DB version</span></td><td>v4.4</td></tr><tr><td><span>Synchronization Id</span></td><td></td></tr><tr><td><span>Lineage</span></td><td></td></tr><tr><td><span>Polyglot models</span></td><td></td></tr><tr><td><span>Comments</span></td><td><div class="docs-markdown"></div></td></tr></tbody></table>

##### 1.1.3 **GrowthTrack** DB Definitions

### <a id="38449220-97dc-11ec-9947-b7f0ab1a4e72"></a>1.1.3.1 Field **role**

##### 1.1.3.1.1 **role** Tree Diagram

![Hackolade image](static/image3.png?raw=true)

##### 1.1.3.1.2 **role** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>role</td></tr><tr><td>Technical name</td><td>role</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>document</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>DBRef</td><td></td></tr><tr><td>Min Properties</td><td></td></tr><tr><td>Max Properties</td><td></td></tr><tr><td>Additional properties</td><td>true</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="containers"></a>

##### 2\. Databases

### <a id="no-bucket"></a>2.1 Database **Undefined Database**

![Hackolade image](static/image4.png?raw=true)

##### 2.1.1 **Undefined Database** Properties

<table class="collection-properties-table"><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Database name</td><td>Undefined Database</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td></td></tr><tr><td>Enable sharding</td><td></td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="no-bucket-children"></a>2.1.2 **Undefined Database** Collections

### <a id="28ec4d90-97e6-11ec-9947-b7f0ab1a4e72"></a>2.1.2.1 Collection **Client**

##### 2.1.2.1.1 **Client** Tree Diagram

![Hackolade image](static/image5.png?raw=true)

##### 2.1.2.1.2 **Client** Properties

<table class="collection-properties-table"><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Collection name</td><td>Client</td></tr><tr><td>Technical name</td><td>clients</td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Database</td><td></td></tr><tr><td>Capped</td><td></td></tr><tr><td>Size</td><td></td></tr><tr><td>Max</td><td></td></tr><tr><td>Storage engine</td><td>WiredTiger</td></tr><tr><td>Config String</td><td></td></tr><tr><td>Validation level</td><td>Off</td></tr><tr><td>Validation action</td><td>Warn</td></tr><tr><td>Additional properties</td><td>false</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

##### 2.1.2.1.3 **Client** Fields

<table><thead><tr><td>Field</td><td>Type</td><td>Req</td><td>Key</td><td>Description</td><td>Comments</td></tr></thead><tbody><tr><td><a href=#39b8b000-97e6-11ec-9947-b7f0ab1a4e72 class="margin-0">client_id</a></td><td class="no-break-word">objectId</td><td>false</td><td>pk, dk</td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#4af7d170-97e6-11ec-9947-b7f0ab1a4e72 class="margin-0">client_name</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#bcb5d0a0-97f0-11ec-8040-bdb9a5c9bfef class="margin-0">address</a></td><td class="no-break-word">document</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#a56bb0d0-97f6-11ec-8040-bdb9a5c9bfef class="margin-5">address&nbsp;line&nbsp;2</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#9248b430-97f6-11ec-8040-bdb9a5c9bfef class="margin-5">address&nbsp;line&nbsp;1</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#66e5fbe0-97f6-11ec-8040-bdb9a5c9bfef class="margin-5">City</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#6ea07040-97f6-11ec-8040-bdb9a5c9bfef class="margin-5">State</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#7c6d4e50-97f6-11ec-8040-bdb9a5c9bfef class="margin-5">country</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#bf951410-97f6-11ec-8040-bdb9a5c9bfef class="margin-0">websiteUrl</a></td><td class="no-break-word">uri</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#f04a1a60-97f6-11ec-8040-bdb9a5c9bfef class="margin-0">POCs</a></td><td class="no-break-word">document</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#fb336080-97f6-11ec-8040-bdb9a5c9bfef class="margin-5">^[a-zA-Z0-9_.-]+$</a></td><td class="no-break-word">array</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#fb37a640-97f6-11ec-8040-bdb9a5c9bfef class="margin-10">[0]</a></td><td class="no-break-word">document</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#0931d5e0-97f7-11ec-8040-bdb9a5c9bfef class="margin-15">email</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#03efdb90-97f7-11ec-8040-bdb9a5c9bfef class="margin-15">name</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#0e40d950-97f7-11ec-8040-bdb9a5c9bfef class="margin-15">mobNo</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#d4b4bdb0-983b-11ec-a11a-61c866bfca96 class="margin-0">subscriptions</a></td><td class="no-break-word">document</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#fe00a3f0-983b-11ec-a11a-61c866bfca96 class="margin-5">rawDataModule</a></td><td class="no-break-word">boolean</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#fe07a8d0-983b-11ec-a11a-61c866bfca96 class="margin-5">leadManageSystem</a></td><td class="no-break-word">boolean</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#fe111eb0-983b-11ec-a11a-61c866bfca96 class="margin-5">AppManageSystem</a></td><td class="no-break-word">boolean</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#15620d90-983c-11ec-a11a-61c866bfca96 class="margin-0">enforcements</a></td><td class="no-break-word">document</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#304b8c80-983c-11ec-a11a-61c866bfca96 class="margin-5">leadLimit</a></td><td class="no-break-word">numeric</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#4142f690-983c-11ec-a11a-61c866bfca96 class="margin-5">counselorLimit</a></td><td class="no-break-word">numeric</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#545d67b0-983c-11ec-a11a-61c866bfca96 class="margin-5">clientManagerLimit</a></td><td class="no-break-word">numeric</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#5cf45960-983c-11ec-a11a-61c866bfca96 class="margin-5">publisherAccountLimit</a></td><td class="no-break-word">numeric</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#9dc89230-983c-11ec-a11a-61c866bfca96 class="margin-0">leads</a></td><td class="no-break-word">document</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#a6752ec0-983c-11ec-a11a-61c866bfca96 class="margin-5">verificationType</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#bb1b48f0-983c-11ec-a11a-61c866bfca96 class="margin-5">leadAPIEnabled</a></td><td class="no-break-word">boolean</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"><p>Can accept leads through API</p></div></td></tr><tr><td><a href=#d50a8960-983c-11ec-a11a-61c866bfca96 class="margin-0">numberOfForms</a></td><td class="no-break-word">numeric</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#e60575e0-983c-11ec-a11a-61c866bfca96 class="margin-0">integrations</a></td><td class="no-break-word">document</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#ed596040-983c-11ec-a11a-61c866bfca96 class="margin-5">withERP</a></td><td class="no-break-word">boolean</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#0ea3de10-983d-11ec-a11a-61c866bfca96 class="margin-5">with3rdPartyApp</a></td><td class="no-break-word">boolean</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#1056be30-983d-11ec-a11a-61c866bfca96 class="margin-5">with3rdPartyTelephony</a></td><td class="no-break-word">boolean</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#38c71180-983d-11ec-a11a-61c866bfca96 class="margin-0">statusInfo</a></td><td class="no-break-word">document</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#5abc7550-983d-11ec-a11a-61c866bfca96 class="margin-5">isActivated</a></td><td class="no-break-word">boolean</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#40b455b0-983d-11ec-a11a-61c866bfca96 class="margin-5">activationDate</a></td><td class="no-break-word">date</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#4ba36830-983d-11ec-a11a-61c866bfca96 class="margin-5">deActivationDate</a></td><td class="no-break-word">date</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#722f1d00-983d-11ec-a11a-61c866bfca96 class="margin-5">creationDate</a></td><td class="no-break-word">date</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"><p>date in which entry was made.This can be different from activation date</p></div></td></tr><tr><td><a href=#92c8e870-983d-11ec-a11a-61c866bfca96 class="margin-0">chargesPerRelease</a></td><td class="no-break-word">document</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#99ecc220-983d-11ec-a11a-61c866bfca96 class="margin-5">forSMS</a></td><td class="no-break-word">numeric</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#b4fab900-983d-11ec-a11a-61c866bfca96 class="margin-5">forEmail</a></td><td class="no-break-word">numeric</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#d6e399b0-983d-11ec-a11a-61c866bfca96 class="margin-0">clientManagerName</a></td><td class="no-break-word">document</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"><p>prePopulated field with client manager informations as received from client</p></div></td></tr><tr><td><a href=#fd060560-983d-11ec-a11a-61c866bfca96 class="margin-5">oneOf</a></td><td class="no-break-word">choice</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#fd210772-983d-11ec-a11a-61c866bfca96 class="margin-10">[0]</a></td><td class="no-break-word">subschema</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#162b8d30-983e-11ec-a11a-61c866bfca96 class="margin-15">client1</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#fd2944d0-983d-11ec-a11a-61c866bfca96 class="margin-10">[1]</a></td><td class="no-break-word">subschema</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#1d4b9650-983e-11ec-a11a-61c866bfca96 class="margin-15">client2</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="39b8b000-97e6-11ec-9947-b7f0ab1a4e72"></a>2.1.2.1.3.1 Field **client\_id**

##### 2.1.2.1.3.1.1 **client\_id** Tree Diagram

![Hackolade image](static/image6.png?raw=true)

##### 2.1.2.1.3.1.2 **client\_id** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>client_id</td></tr><tr><td>Technical name</td><td>client_id</td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>objectId</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td>true</td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="4af7d170-97e6-11ec-9947-b7f0ab1a4e72"></a>2.1.2.1.3.2 Field **client\_name**

##### 2.1.2.1.3.2.1 **client\_name** Tree Diagram

![Hackolade image](static/image7.png?raw=true)

##### 2.1.2.1.3.2.2 **client\_name** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>client_name</td></tr><tr><td>Technical name</td><td>client_name</td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td>GrowthTrack</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="bcb5d0a0-97f0-11ec-8040-bdb9a5c9bfef"></a>2.1.2.1.3.3 Field **address**

##### 2.1.2.1.3.3.1 **address** Tree Diagram

![Hackolade image](static/image8.png?raw=true)

##### 2.1.2.1.3.3.2 **address** Hierarchy

Parent field: **Client**

Child field(s):

<table class="field-properties-table"><thead><tr><td>Field</td><td>Type</td><td>Req</td><td>Key</td><td>Description</td><td>Comments</td></tr></thead><tbody><tr><td><a href=#a56bb0d0-97f6-11ec-8040-bdb9a5c9bfef class="margin-NaN">address&nbsp;line&nbsp;2</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#9248b430-97f6-11ec-8040-bdb9a5c9bfef class="margin-NaN">address&nbsp;line&nbsp;1</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#66e5fbe0-97f6-11ec-8040-bdb9a5c9bfef class="margin-NaN">City</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#6ea07040-97f6-11ec-8040-bdb9a5c9bfef class="margin-NaN">State</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#7c6d4e50-97f6-11ec-8040-bdb9a5c9bfef class="margin-NaN">country</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr></tbody></table>

##### 2.1.2.1.3.3.3 **address** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>address</td></tr><tr><td>Technical name</td><td>addrss</td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>document</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>DBRef</td><td></td></tr><tr><td>Min Properties</td><td></td></tr><tr><td>Max Properties</td><td></td></tr><tr><td>Additional properties</td><td>false</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="a56bb0d0-97f6-11ec-8040-bdb9a5c9bfef"></a>2.1.2.1.3.4 Field **address line 2**

##### 2.1.2.1.3.4.1 **address line 2** Tree Diagram

![Hackolade image](static/image9.png?raw=true)

##### 2.1.2.1.3.4.2 **address line 2** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>address line 2</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="9248b430-97f6-11ec-8040-bdb9a5c9bfef"></a>2.1.2.1.3.5 Field **address line 1**

##### 2.1.2.1.3.5.1 **address line 1** Tree Diagram

![Hackolade image](static/image10.png?raw=true)

##### 2.1.2.1.3.5.2 **address line 1** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>address line 1</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="66e5fbe0-97f6-11ec-8040-bdb9a5c9bfef"></a>2.1.2.1.3.6 Field **City**

##### 2.1.2.1.3.6.1 **City** Tree Diagram

![Hackolade image](static/image11.png?raw=true)

##### 2.1.2.1.3.6.2 **City** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>City</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="6ea07040-97f6-11ec-8040-bdb9a5c9bfef"></a>2.1.2.1.3.7 Field **State**

##### 2.1.2.1.3.7.1 **State** Tree Diagram

![Hackolade image](static/image12.png?raw=true)

##### 2.1.2.1.3.7.2 **State** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>State</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="7c6d4e50-97f6-11ec-8040-bdb9a5c9bfef"></a>2.1.2.1.3.8 Field **country**

##### 2.1.2.1.3.8.1 **country** Tree Diagram

![Hackolade image](static/image13.png?raw=true)

##### 2.1.2.1.3.8.2 **country** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>country</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="bf951410-97f6-11ec-8040-bdb9a5c9bfef"></a>2.1.2.1.3.9 Field **websiteUrl**

##### 2.1.2.1.3.9.1 **websiteUrl** Tree Diagram

![Hackolade image](static/image14.png?raw=true)

##### 2.1.2.1.3.9.2 **websiteUrl** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>websiteUrl</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td>uri</td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="f04a1a60-97f6-11ec-8040-bdb9a5c9bfef"></a>2.1.2.1.3.10 Field **POCs**

##### 2.1.2.1.3.10.1 **POCs** Tree Diagram

![Hackolade image](static/image15.png?raw=true)

##### 2.1.2.1.3.10.2 **POCs** Hierarchy

Parent field: **Client**

Child field(s):

<table class="field-properties-table"><thead><tr><td>Field</td><td>Type</td><td>Req</td><td>Key</td><td>Description</td><td>Comments</td></tr></thead><tbody><tr><td><a href=#fb336080-97f6-11ec-8040-bdb9a5c9bfef class="margin-NaN">^[a-zA-Z0-9_.-]+$</a></td><td class="no-break-word">array</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr></tbody></table>

##### 2.1.2.1.3.10.3 **POCs** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>POCs</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>document</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>DBRef</td><td></td></tr><tr><td>Min Properties</td><td></td></tr><tr><td>Max Properties</td><td></td></tr><tr><td>Additional properties</td><td>false</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="fb336080-97f6-11ec-8040-bdb9a5c9bfef"></a>2.1.2.1.3.11 Field **^\[a-zA-Z0-9\_.-\]+$**

##### 2.1.2.1.3.11.1 **^\[a-zA-Z0-9\_.-\]+$** Tree Diagram

![Hackolade image](static/image16.png?raw=true)

##### 2.1.2.1.3.11.2 **^\[a-zA-Z0-9\_.-\]+$** Hierarchy

Parent field: **POCs**

Child field(s):

<table class="field-properties-table"><thead><tr><td>Field</td><td>Type</td><td>Req</td><td>Key</td><td>Description</td><td>Comments</td></tr></thead><tbody><tr><td><a href=#fb37a640-97f6-11ec-8040-bdb9a5c9bfef class="margin-NaN">[0]</a></td><td class="no-break-word">document</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr></tbody></table>

##### 2.1.2.1.3.11.3 **^\[a-zA-Z0-9\_.-\]+$** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>^[a-zA-Z0-9_.-]+$</td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Sample Name</td><td></td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>array</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Min items</td><td></td></tr><tr><td>Max items</td><td></td></tr><tr><td>Unique items</td><td></td></tr><tr><td>Additional items</td><td>true</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="fb37a640-97f6-11ec-8040-bdb9a5c9bfef"></a>2.1.2.1.3.12 Field **\[0\]**

##### 2.1.2.1.3.12.1 **\[0\]** Tree Diagram

![Hackolade image](static/image17.png?raw=true)

##### 2.1.2.1.3.12.2 **\[0\]** Hierarchy

Parent field: **^\[a-zA-Z0-9\_.-\]+$**

Child field(s):

<table class="field-properties-table"><thead><tr><td>Field</td><td>Type</td><td>Req</td><td>Key</td><td>Description</td><td>Comments</td></tr></thead><tbody><tr><td><a href=#0931d5e0-97f7-11ec-8040-bdb9a5c9bfef class="margin-NaN">email</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#03efdb90-97f7-11ec-8040-bdb9a5c9bfef class="margin-NaN">name</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#0e40d950-97f7-11ec-8040-bdb9a5c9bfef class="margin-NaN">mobNo</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr></tbody></table>

##### 2.1.2.1.3.12.3 **\[0\]** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Display name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>document</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>DBRef</td><td></td></tr><tr><td>Min Properties</td><td></td></tr><tr><td>Max Properties</td><td></td></tr><tr><td>Additional properties</td><td>false</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="0931d5e0-97f7-11ec-8040-bdb9a5c9bfef"></a>2.1.2.1.3.13 Field **email**

##### 2.1.2.1.3.13.1 **email** Tree Diagram

![Hackolade image](static/image18.png?raw=true)

##### 2.1.2.1.3.13.2 **email** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>email</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="03efdb90-97f7-11ec-8040-bdb9a5c9bfef"></a>2.1.2.1.3.14 Field **name**

##### 2.1.2.1.3.14.1 **name** Tree Diagram

![Hackolade image](static/image19.png?raw=true)

##### 2.1.2.1.3.14.2 **name** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>name</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="0e40d950-97f7-11ec-8040-bdb9a5c9bfef"></a>2.1.2.1.3.15 Field **mobNo**

##### 2.1.2.1.3.15.1 **mobNo** Tree Diagram

![Hackolade image](static/image20.png?raw=true)

##### 2.1.2.1.3.15.2 **mobNo** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>mobNo</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="d4b4bdb0-983b-11ec-a11a-61c866bfca96"></a>2.1.2.1.3.16 Field **subscriptions**

##### 2.1.2.1.3.16.1 **subscriptions** Tree Diagram

![Hackolade image](static/image21.png?raw=true)

##### 2.1.2.1.3.16.2 **subscriptions** Hierarchy

Parent field: **Client**

Child field(s):

<table class="field-properties-table"><thead><tr><td>Field</td><td>Type</td><td>Req</td><td>Key</td><td>Description</td><td>Comments</td></tr></thead><tbody><tr><td><a href=#fe00a3f0-983b-11ec-a11a-61c866bfca96 class="margin-NaN">rawDataModule</a></td><td class="no-break-word">boolean</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#fe07a8d0-983b-11ec-a11a-61c866bfca96 class="margin-NaN">leadManageSystem</a></td><td class="no-break-word">boolean</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#fe111eb0-983b-11ec-a11a-61c866bfca96 class="margin-NaN">AppManageSystem</a></td><td class="no-break-word">boolean</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr></tbody></table>

##### 2.1.2.1.3.16.3 **subscriptions** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>subscriptions</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>document</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>DBRef</td><td></td></tr><tr><td>Min Properties</td><td></td></tr><tr><td>Max Properties</td><td></td></tr><tr><td>Additional properties</td><td>false</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="fe00a3f0-983b-11ec-a11a-61c866bfca96"></a>2.1.2.1.3.17 Field **rawDataModule**

##### 2.1.2.1.3.17.1 **rawDataModule** Tree Diagram

![Hackolade image](static/image22.png?raw=true)

##### 2.1.2.1.3.17.2 **rawDataModule** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>rawDataModule</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>boolean</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="fe07a8d0-983b-11ec-a11a-61c866bfca96"></a>2.1.2.1.3.18 Field **leadManageSystem**

##### 2.1.2.1.3.18.1 **leadManageSystem** Tree Diagram

![Hackolade image](static/image23.png?raw=true)

##### 2.1.2.1.3.18.2 **leadManageSystem** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>leadManageSystem</td></tr><tr><td>Technical name</td><td>Lead Management System</td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>boolean</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="fe111eb0-983b-11ec-a11a-61c866bfca96"></a>2.1.2.1.3.19 Field **AppManageSystem**

##### 2.1.2.1.3.19.1 **AppManageSystem** Tree Diagram

![Hackolade image](static/image24.png?raw=true)

##### 2.1.2.1.3.19.2 **AppManageSystem** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>AppManageSystem</td></tr><tr><td>Technical name</td><td>Application Management System</td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>boolean</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="15620d90-983c-11ec-a11a-61c866bfca96"></a>2.1.2.1.3.20 Field **enforcements**

##### 2.1.2.1.3.20.1 **enforcements** Tree Diagram

![Hackolade image](static/image25.png?raw=true)

##### 2.1.2.1.3.20.2 **enforcements** Hierarchy

Parent field: **Client**

Child field(s):

<table class="field-properties-table"><thead><tr><td>Field</td><td>Type</td><td>Req</td><td>Key</td><td>Description</td><td>Comments</td></tr></thead><tbody><tr><td><a href=#304b8c80-983c-11ec-a11a-61c866bfca96 class="margin-NaN">leadLimit</a></td><td class="no-break-word">numeric</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#4142f690-983c-11ec-a11a-61c866bfca96 class="margin-NaN">counselorLimit</a></td><td class="no-break-word">numeric</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#545d67b0-983c-11ec-a11a-61c866bfca96 class="margin-NaN">clientManagerLimit</a></td><td class="no-break-word">numeric</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#5cf45960-983c-11ec-a11a-61c866bfca96 class="margin-NaN">publisherAccountLimit</a></td><td class="no-break-word">numeric</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr></tbody></table>

##### 2.1.2.1.3.20.3 **enforcements** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>enforcements</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>document</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>DBRef</td><td></td></tr><tr><td>Min Properties</td><td></td></tr><tr><td>Max Properties</td><td></td></tr><tr><td>Additional properties</td><td>false</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="304b8c80-983c-11ec-a11a-61c866bfca96"></a>2.1.2.1.3.21 Field **leadLimit**

##### 2.1.2.1.3.21.1 **leadLimit** Tree Diagram

![Hackolade image](static/image26.png?raw=true)

##### 2.1.2.1.3.21.2 **leadLimit** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>leadLimit</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>numeric</td></tr><tr><td>Subtype</td><td></td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Unit</td><td></td></tr><tr><td>Min value</td><td></td></tr><tr><td>Excl min</td><td></td></tr><tr><td>Max value</td><td></td></tr><tr><td>Excl max</td><td></td></tr><tr><td>Multiple of</td><td></td></tr><tr><td>Divisible by</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="4142f690-983c-11ec-a11a-61c866bfca96"></a>2.1.2.1.3.22 Field **counselorLimit**

##### 2.1.2.1.3.22.1 **counselorLimit** Tree Diagram

![Hackolade image](static/image27.png?raw=true)

##### 2.1.2.1.3.22.2 **counselorLimit** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>counselorLimit</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>numeric</td></tr><tr><td>Subtype</td><td></td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Unit</td><td></td></tr><tr><td>Min value</td><td></td></tr><tr><td>Excl min</td><td></td></tr><tr><td>Max value</td><td></td></tr><tr><td>Excl max</td><td></td></tr><tr><td>Multiple of</td><td></td></tr><tr><td>Divisible by</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="545d67b0-983c-11ec-a11a-61c866bfca96"></a>2.1.2.1.3.23 Field **clientManagerLimit**

##### 2.1.2.1.3.23.1 **clientManagerLimit** Tree Diagram

![Hackolade image](static/image28.png?raw=true)

##### 2.1.2.1.3.23.2 **clientManagerLimit** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>clientManagerLimit</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>numeric</td></tr><tr><td>Subtype</td><td></td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Unit</td><td></td></tr><tr><td>Min value</td><td></td></tr><tr><td>Excl min</td><td></td></tr><tr><td>Max value</td><td></td></tr><tr><td>Excl max</td><td></td></tr><tr><td>Multiple of</td><td></td></tr><tr><td>Divisible by</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="5cf45960-983c-11ec-a11a-61c866bfca96"></a>2.1.2.1.3.24 Field **publisherAccountLimit**

##### 2.1.2.1.3.24.1 **publisherAccountLimit** Tree Diagram

![Hackolade image](static/image29.png?raw=true)

##### 2.1.2.1.3.24.2 **publisherAccountLimit** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>publisherAccountLimit</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>numeric</td></tr><tr><td>Subtype</td><td></td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Unit</td><td></td></tr><tr><td>Min value</td><td></td></tr><tr><td>Excl min</td><td></td></tr><tr><td>Max value</td><td></td></tr><tr><td>Excl max</td><td></td></tr><tr><td>Multiple of</td><td></td></tr><tr><td>Divisible by</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="9dc89230-983c-11ec-a11a-61c866bfca96"></a>2.1.2.1.3.25 Field **leads**

##### 2.1.2.1.3.25.1 **leads** Tree Diagram

![Hackolade image](static/image30.png?raw=true)

##### 2.1.2.1.3.25.2 **leads** Hierarchy

Parent field: **Client**

Child field(s):

<table class="field-properties-table"><thead><tr><td>Field</td><td>Type</td><td>Req</td><td>Key</td><td>Description</td><td>Comments</td></tr></thead><tbody><tr><td><a href=#a6752ec0-983c-11ec-a11a-61c866bfca96 class="margin-NaN">verificationType</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#bb1b48f0-983c-11ec-a11a-61c866bfca96 class="margin-NaN">leadAPIEnabled</a></td><td class="no-break-word">boolean</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"><p>Can accept leads through API</p></div></td></tr></tbody></table>

##### 2.1.2.1.3.25.3 **leads** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>leads</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>document</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>DBRef</td><td></td></tr><tr><td>Min Properties</td><td></td></tr><tr><td>Max Properties</td><td></td></tr><tr><td>Additional properties</td><td>false</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="a6752ec0-983c-11ec-a11a-61c866bfca96"></a>2.1.2.1.3.26 Field **verificationType**

##### 2.1.2.1.3.26.1 **verificationType** Tree Diagram

![Hackolade image](static/image31.png?raw=true)

##### 2.1.2.1.3.26.2 **verificationType** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>verificationType</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td>"OTP"</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="bb1b48f0-983c-11ec-a11a-61c866bfca96"></a>2.1.2.1.3.27 Field **leadAPIEnabled**

##### 2.1.2.1.3.27.1 **leadAPIEnabled** Tree Diagram

![Hackolade image](static/image32.png?raw=true)

##### 2.1.2.1.3.27.2 **leadAPIEnabled** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>leadAPIEnabled</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>boolean</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"><p>Can accept leads through API</p></div></td></tr></tbody></table>

### <a id="d50a8960-983c-11ec-a11a-61c866bfca96"></a>2.1.2.1.3.28 Field **numberOfForms**

##### 2.1.2.1.3.28.1 **numberOfForms** Tree Diagram

![Hackolade image](static/image33.png?raw=true)

##### 2.1.2.1.3.28.2 **numberOfForms** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>numberOfForms</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>numeric</td></tr><tr><td>Subtype</td><td></td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Unit</td><td></td></tr><tr><td>Min value</td><td></td></tr><tr><td>Excl min</td><td></td></tr><tr><td>Max value</td><td></td></tr><tr><td>Excl max</td><td></td></tr><tr><td>Multiple of</td><td></td></tr><tr><td>Divisible by</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="e60575e0-983c-11ec-a11a-61c866bfca96"></a>2.1.2.1.3.29 Field **integrations**

##### 2.1.2.1.3.29.1 **integrations** Tree Diagram

![Hackolade image](static/image34.png?raw=true)

##### 2.1.2.1.3.29.2 **integrations** Hierarchy

Parent field: **Client**

Child field(s):

<table class="field-properties-table"><thead><tr><td>Field</td><td>Type</td><td>Req</td><td>Key</td><td>Description</td><td>Comments</td></tr></thead><tbody><tr><td><a href=#ed596040-983c-11ec-a11a-61c866bfca96 class="margin-NaN">withERP</a></td><td class="no-break-word">boolean</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#0ea3de10-983d-11ec-a11a-61c866bfca96 class="margin-NaN">with3rdPartyApp</a></td><td class="no-break-word">boolean</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#1056be30-983d-11ec-a11a-61c866bfca96 class="margin-NaN">with3rdPartyTelephony</a></td><td class="no-break-word">boolean</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr></tbody></table>

##### 2.1.2.1.3.29.3 **integrations** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>integrations</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>document</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>DBRef</td><td></td></tr><tr><td>Min Properties</td><td></td></tr><tr><td>Max Properties</td><td></td></tr><tr><td>Additional properties</td><td>false</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="ed596040-983c-11ec-a11a-61c866bfca96"></a>2.1.2.1.3.30 Field **withERP**

##### 2.1.2.1.3.30.1 **withERP** Tree Diagram

![Hackolade image](static/image35.png?raw=true)

##### 2.1.2.1.3.30.2 **withERP** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>withERP</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>boolean</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Sample</td><td>false</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="0ea3de10-983d-11ec-a11a-61c866bfca96"></a>2.1.2.1.3.31 Field **with3rdPartyApp**

##### 2.1.2.1.3.31.1 **with3rdPartyApp** Tree Diagram

![Hackolade image](static/image36.png?raw=true)

##### 2.1.2.1.3.31.2 **with3rdPartyApp** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>with3rdPartyApp</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>boolean</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Sample</td><td>true</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="1056be30-983d-11ec-a11a-61c866bfca96"></a>2.1.2.1.3.32 Field **with3rdPartyTelephony**

##### 2.1.2.1.3.32.1 **with3rdPartyTelephony** Tree Diagram

![Hackolade image](static/image37.png?raw=true)

##### 2.1.2.1.3.32.2 **with3rdPartyTelephony** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>with3rdPartyTelephony</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>boolean</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Sample</td><td>true</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="38c71180-983d-11ec-a11a-61c866bfca96"></a>2.1.2.1.3.33 Field **statusInfo**

##### 2.1.2.1.3.33.1 **statusInfo** Tree Diagram

![Hackolade image](static/image38.png?raw=true)

##### 2.1.2.1.3.33.2 **statusInfo** Hierarchy

Parent field: **Client**

Child field(s):

<table class="field-properties-table"><thead><tr><td>Field</td><td>Type</td><td>Req</td><td>Key</td><td>Description</td><td>Comments</td></tr></thead><tbody><tr><td><a href=#5abc7550-983d-11ec-a11a-61c866bfca96 class="margin-NaN">isActivated</a></td><td class="no-break-word">boolean</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#40b455b0-983d-11ec-a11a-61c866bfca96 class="margin-NaN">activationDate</a></td><td class="no-break-word">date</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#4ba36830-983d-11ec-a11a-61c866bfca96 class="margin-NaN">deActivationDate</a></td><td class="no-break-word">date</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#722f1d00-983d-11ec-a11a-61c866bfca96 class="margin-NaN">creationDate</a></td><td class="no-break-word">date</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"><p>date in which entry was made.This can be different from activation date</p></div></td></tr></tbody></table>

##### 2.1.2.1.3.33.3 **statusInfo** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>statusInfo</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>document</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>DBRef</td><td></td></tr><tr><td>Min Properties</td><td></td></tr><tr><td>Max Properties</td><td></td></tr><tr><td>Additional properties</td><td>false</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="5abc7550-983d-11ec-a11a-61c866bfca96"></a>2.1.2.1.3.34 Field **isActivated**

##### 2.1.2.1.3.34.1 **isActivated** Tree Diagram

![Hackolade image](static/image39.png?raw=true)

##### 2.1.2.1.3.34.2 **isActivated** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>isActivated</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>boolean</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Sample</td><td>true</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="40b455b0-983d-11ec-a11a-61c866bfca96"></a>2.1.2.1.3.35 Field **activationDate**

##### 2.1.2.1.3.35.1 **activationDate** Tree Diagram

![Hackolade image](static/image40.png?raw=true)

##### 2.1.2.1.3.35.2 **activationDate** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>activationDate</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>date</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td>false</td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Now</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="4ba36830-983d-11ec-a11a-61c866bfca96"></a>2.1.2.1.3.36 Field **deActivationDate**

##### 2.1.2.1.3.36.1 **deActivationDate** Tree Diagram

![Hackolade image](static/image41.png?raw=true)

##### 2.1.2.1.3.36.2 **deActivationDate** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>deActivationDate</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>date</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td>false</td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Now</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="722f1d00-983d-11ec-a11a-61c866bfca96"></a>2.1.2.1.3.37 Field **creationDate**

##### 2.1.2.1.3.37.1 **creationDate** Tree Diagram

![Hackolade image](static/image42.png?raw=true)

##### 2.1.2.1.3.37.2 **creationDate** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>creationDate</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>date</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td>false</td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Now</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"><p>date in which entry was made.This can be different from activation date</p></div></td></tr></tbody></table>

### <a id="92c8e870-983d-11ec-a11a-61c866bfca96"></a>2.1.2.1.3.38 Field **chargesPerRelease**

##### 2.1.2.1.3.38.1 **chargesPerRelease** Tree Diagram

![Hackolade image](static/image43.png?raw=true)

##### 2.1.2.1.3.38.2 **chargesPerRelease** Hierarchy

Parent field: **Client**

Child field(s):

<table class="field-properties-table"><thead><tr><td>Field</td><td>Type</td><td>Req</td><td>Key</td><td>Description</td><td>Comments</td></tr></thead><tbody><tr><td><a href=#99ecc220-983d-11ec-a11a-61c866bfca96 class="margin-NaN">forSMS</a></td><td class="no-break-word">numeric</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#b4fab900-983d-11ec-a11a-61c866bfca96 class="margin-NaN">forEmail</a></td><td class="no-break-word">numeric</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr></tbody></table>

##### 2.1.2.1.3.38.3 **chargesPerRelease** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>chargesPerRelease</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>document</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>DBRef</td><td></td></tr><tr><td>Min Properties</td><td></td></tr><tr><td>Max Properties</td><td></td></tr><tr><td>Additional properties</td><td>false</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="99ecc220-983d-11ec-a11a-61c866bfca96"></a>2.1.2.1.3.39 Field **forSMS**

##### 2.1.2.1.3.39.1 **forSMS** Tree Diagram

![Hackolade image](static/image44.png?raw=true)

##### 2.1.2.1.3.39.2 **forSMS** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>forSMS</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>numeric</td></tr><tr><td>Subtype</td><td></td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Unit</td><td></td></tr><tr><td>Min value</td><td></td></tr><tr><td>Excl min</td><td></td></tr><tr><td>Max value</td><td></td></tr><tr><td>Excl max</td><td></td></tr><tr><td>Multiple of</td><td></td></tr><tr><td>Divisible by</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="b4fab900-983d-11ec-a11a-61c866bfca96"></a>2.1.2.1.3.40 Field **forEmail**

##### 2.1.2.1.3.40.1 **forEmail** Tree Diagram

![Hackolade image](static/image45.png?raw=true)

##### 2.1.2.1.3.40.2 **forEmail** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>forEmail</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>numeric</td></tr><tr><td>Subtype</td><td></td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Unit</td><td></td></tr><tr><td>Min value</td><td></td></tr><tr><td>Excl min</td><td></td></tr><tr><td>Max value</td><td></td></tr><tr><td>Excl max</td><td></td></tr><tr><td>Multiple of</td><td></td></tr><tr><td>Divisible by</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="d6e399b0-983d-11ec-a11a-61c866bfca96"></a>2.1.2.1.3.41 Field **clientManagerName**

##### 2.1.2.1.3.41.1 **clientManagerName** Tree Diagram

![Hackolade image](static/image46.png?raw=true)

##### 2.1.2.1.3.41.2 **clientManagerName** Hierarchy

Parent field: **Client**

Child field(s):

<table class="field-properties-table"><thead><tr><td>Field</td><td>Type</td><td>Req</td><td>Key</td><td>Description</td><td>Comments</td></tr></thead><tbody><tr><td><a href=#fd060560-983d-11ec-a11a-61c866bfca96 class="margin-NaN">oneOf</a></td><td class="no-break-word">choice</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr></tbody></table>

##### 2.1.2.1.3.41.3 **clientManagerName** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>clientManagerName</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>document</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>DBRef</td><td></td></tr><tr><td>Min Properties</td><td></td></tr><tr><td>Max Properties</td><td></td></tr><tr><td>Additional properties</td><td>true</td></tr><tr><td>Comments</td><td><div class="docs-markdown"><p>prePopulated field with client manager informations as received from client</p></div></td></tr></tbody></table>

### <a id="fd060560-983d-11ec-a11a-61c866bfca96"></a>2.1.2.1.3.42 Field **oneOf**

##### 2.1.2.1.3.42.1 **oneOf** Tree Diagram

![Hackolade image](static/image47.png?raw=true)

##### 2.1.2.1.3.42.2 **oneOf** Hierarchy

Parent field: **clientManagerName**

Child field(s):

<table class="field-properties-table"><thead><tr><td>Field</td><td>Type</td><td>Req</td><td>Key</td><td>Description</td><td>Comments</td></tr></thead><tbody><tr><td><a href=#fd210772-983d-11ec-a11a-61c866bfca96 class="margin-NaN">[0]</a></td><td class="no-break-word">document</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#fd2944d0-983d-11ec-a11a-61c866bfca96 class="margin-NaN">[1]</a></td><td class="no-break-word">document</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr></tbody></table>

##### 2.1.2.1.3.42.3 **oneOf** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Choice</td><td>oneOf</td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="fd210772-983d-11ec-a11a-61c866bfca96"></a>2.1.2.1.3.43 Field **\[0\]**

##### 2.1.2.1.3.43.1 **\[0\]** Tree Diagram

![Hackolade image](static/image48.png?raw=true)

##### 2.1.2.1.3.43.2 **\[0\]** Hierarchy

Parent field: **oneOf**

Child field(s):

<table class="field-properties-table"><thead><tr><td>Field</td><td>Type</td><td>Req</td><td>Key</td><td>Description</td><td>Comments</td></tr></thead><tbody><tr><td><a href=#162b8d30-983e-11ec-a11a-61c866bfca96 class="margin-NaN">client1</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr></tbody></table>

##### 2.1.2.1.3.43.3 **\[0\]** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Display name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>document</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>DBRef</td><td></td></tr><tr><td>Min Properties</td><td></td></tr><tr><td>Max Properties</td><td></td></tr><tr><td>Additional properties</td><td>true</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="162b8d30-983e-11ec-a11a-61c866bfca96"></a>2.1.2.1.3.44 Field **client1**

##### 2.1.2.1.3.44.1 **client1** Tree Diagram

![Hackolade image](static/image49.png?raw=true)

##### 2.1.2.1.3.44.2 **client1** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>client1</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="fd2944d0-983d-11ec-a11a-61c866bfca96"></a>2.1.2.1.3.45 Field **\[1\]**

##### 2.1.2.1.3.45.1 **\[1\]** Tree Diagram

![Hackolade image](static/image50.png?raw=true)

##### 2.1.2.1.3.45.2 **\[1\]** Hierarchy

Parent field: **oneOf**

Child field(s):

<table class="field-properties-table"><thead><tr><td>Field</td><td>Type</td><td>Req</td><td>Key</td><td>Description</td><td>Comments</td></tr></thead><tbody><tr><td><a href=#1d4b9650-983e-11ec-a11a-61c866bfca96 class="margin-NaN">client2</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr></tbody></table>

##### 2.1.2.1.3.45.3 **\[1\]** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Display name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>document</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>DBRef</td><td></td></tr><tr><td>Min Properties</td><td></td></tr><tr><td>Max Properties</td><td></td></tr><tr><td>Additional properties</td><td>true</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="1d4b9650-983e-11ec-a11a-61c866bfca96"></a>2.1.2.1.3.46 Field **client2**

##### 2.1.2.1.3.46.1 **client2** Tree Diagram

![Hackolade image](static/image51.png?raw=true)

##### 2.1.2.1.3.46.2 **client2** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>client2</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

##### 2.1.2.1.4 **Client** Definitions

### <a id="817386e0-97f0-11ec-8040-bdb9a5c9bfef"></a>2.1.2.1.4.1 Field **address**

##### 2.1.2.1.4.1.1 **address** Tree Diagram

![Hackolade image](static/image52.png?raw=true)

##### 2.1.2.1.4.1.2 **address** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>address</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

##### 2.1.2.1.5 **Client** JSON Schema

```
{
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "title": "Client",
    "properties": {
        "client_id": {
            "type": "string",
            "title": "client_id",
            "pattern": "^[a-fA-F0-9]{24}$"
        },
        "client_name": {
            "type": "string",
            "title": "client_name"
        },
        "addrss": {
            "type": "object",
            "title": "address",
            "properties": {
                "address line 2": {
                    "type": "string"
                },
                "address line 1": {
                    "type": "string"
                },
                "City": {
                    "type": "string"
                },
                "State": {
                    "type": "string"
                },
                "country": {
                    "type": "string"
                }
            },
            "additionalProperties": false
        },
        "websiteUrl": {
            "type": "string",
            "format": "uri"
        },
        "POCs": {
            "type": "object",
            "additionalProperties": false,
            "patternProperties": {
                "^[a-zA-Z0-9_.-]+$": {
                    "type": "array",
                    "additionalItems": true,
                    "items": {
                        "type": "object",
                        "properties": {
                            "email": {
                                "type": "string"
                            },
                            "name": {
                                "type": "string"
                            },
                            "mobNo": {
                                "type": "string"
                            }
                        },
                        "additionalProperties": false
                    }
                }
            }
        },
        "subscriptions": {
            "type": "object",
            "properties": {
                "rawDataModule": {
                    "type": "boolean"
                },
                "Lead Management System": {
                    "type": "boolean",
                    "title": "leadManageSystem"
                },
                "Application Management System": {
                    "type": "boolean",
                    "title": "AppManageSystem"
                }
            },
            "additionalProperties": false
        },
        "enforcements": {
            "type": "object",
            "properties": {
                "leadLimit": {
                    "type": "number"
                },
                "counselorLimit": {
                    "type": "number"
                },
                "clientManagerLimit": {
                    "type": "number"
                },
                "publisherAccountLimit": {
                    "type": "number"
                }
            },
            "additionalProperties": false
        },
        "leads": {
            "type": "object",
            "properties": {
                "verificationType": {
                    "type": "string"
                },
                "leadAPIEnabled": {
                    "type": "boolean"
                }
            },
            "additionalProperties": false
        },
        "numberOfForms": {
            "type": "number"
        },
        "integrations": {
            "type": "object",
            "properties": {
                "withERP": {
                    "type": "boolean"
                },
                "with3rdPartyApp": {
                    "type": "boolean"
                },
                "with3rdPartyTelephony": {
                    "type": "boolean"
                }
            },
            "additionalProperties": false
        },
        "statusInfo": {
            "type": "object",
            "properties": {
                "isActivated": {
                    "type": "boolean"
                },
                "activationDate": {
                    "type": "string",
                    "format": "date-time"
                },
                "deActivationDate": {
                    "type": "string",
                    "format": "date-time"
                },
                "creationDate": {
                    "type": "string",
                    "format": "date-time"
                }
            },
            "additionalProperties": false
        },
        "chargesPerRelease": {
            "type": "object",
            "properties": {
                "forSMS": {
                    "type": "number"
                },
                "forEmail": {
                    "type": "number"
                }
            },
            "additionalProperties": false
        },
        "clientManagerName": {
            "type": "object",
            "additionalProperties": true,
            "oneOf": [
                {
                    "type": "object",
                    "properties": {
                        "client1": {
                            "type": "string"
                        }
                    },
                    "additionalProperties": true
                },
                {
                    "type": "object",
                    "properties": {
                        "client2": {
                            "type": "string"
                        }
                    },
                    "additionalProperties": true
                }
            ]
        }
    },
    "definitions": {
        "address": {
            "type": "string"
        }
    },
    "additionalProperties": false
}
```

##### 2.1.2.1.6 **Client** JSON data

```
{
    "client_id": ObjectId("507f1f77bcf86cd799439011"),
    "client_name": "GrowthTrack",
    "addrss": {
        "address line 2": "Lorem",
        "address line 1": "Lorem",
        "City": "Lorem",
        "State": "Lorem",
        "country": "Lorem"
    },
    "websiteUrl": "./resource.txt#frag01",
    "POCs": {},
    "subscriptions": {
        "rawDataModule": true,
        "Lead Management System": true,
        "Application Management System": true
    },
    "enforcements": {
        "leadLimit": -53,
        "counselorLimit": -63,
        "clientManagerLimit": 45,
        "publisherAccountLimit": 68
    },
    "leads": {
        "verificationType": "'OTP'",
        "leadAPIEnabled": true
    },
    "numberOfForms": 67,
    "integrations": {
        "withERP": false,
        "with3rdPartyApp": true,
        "with3rdPartyTelephony": true
    },
    "statusInfo": {
        "isActivated": true,
        "activationDate": ISODate("2016-04-08T15:06:21.595Z"),
        "deActivationDate": ISODate("2016-04-08T15:06:21.595Z"),
        "creationDate": ISODate("2016-04-08T15:06:21.595Z")
    },
    "chargesPerRelease": {
        "forSMS": -93,
        "forEmail": 10
    },
    "clientManagerName": {
        "client1": "Lorem"
    }
}
```

##### 2.1.2.1.7 **Client** Target Script

```
db.createCollection("clients", {
    "storageEngine": {
        "wiredTiger": {}
    },
    "capped": false,
    "validator": {
        "$jsonSchema": {
            "bsonType": "object",
            "title": "Client",
            "properties": {
                "_id": {
                    "bsonType": "objectId"
                },
                "client_id": {
                    "bsonType": "objectId",
                    "title": "client_id"
                },
                "client_name": {
                    "bsonType": "string",
                    "title": "client_name"
                },
                "addrss": {
                    "bsonType": "object",
                    "title": "address",
                    "properties": {
                        "address line 2": {
                            "bsonType": "string"
                        },
                        "address line 1": {
                            "bsonType": "string"
                        },
                        "City": {
                            "bsonType": "string"
                        },
                        "State": {
                            "bsonType": "string"
                        },
                        "country": {
                            "bsonType": "string"
                        }
                    },
                    "additionalProperties": false
                },
                "websiteUrl": {
                    "bsonType": "string"
                },
                "POCs": {
                    "bsonType": "object",
                    "additionalProperties": false,
                    "patternProperties": {
                        "^[a-zA-Z0-9_.-]+$": {
                            "bsonType": "array",
                            "additionalItems": true,
                            "items": {
                                "bsonType": "object",
                                "properties": {
                                    "email": {
                                        "bsonType": "string"
                                    },
                                    "name": {
                                        "bsonType": "string"
                                    },
                                    "mobNo": {
                                        "bsonType": "string"
                                    }
                                },
                                "additionalProperties": false
                            }
                        }
                    }
                },
                "subscriptions": {
                    "bsonType": "object",
                    "properties": {
                        "rawDataModule": {
                            "bsonType": "bool"
                        },
                        "Lead Management System": {
                            "bsonType": "bool",
                            "title": "leadManageSystem"
                        },
                        "Application Management System": {
                            "bsonType": "bool",
                            "title": "AppManageSystem"
                        }
                    },
                    "additionalProperties": false
                },
                "enforcements": {
                    "bsonType": "object",
                    "properties": {
                        "leadLimit": {
                            "bsonType": "number"
                        },
                        "counselorLimit": {
                            "bsonType": "number"
                        },
                        "clientManagerLimit": {
                            "bsonType": "number"
                        },
                        "publisherAccountLimit": {
                            "bsonType": "number"
                        }
                    },
                    "additionalProperties": false
                },
                "leads": {
                    "bsonType": "object",
                    "properties": {
                        "verificationType": {
                            "bsonType": "string"
                        },
                        "leadAPIEnabled": {
                            "bsonType": "bool"
                        }
                    },
                    "additionalProperties": false
                },
                "numberOfForms": {
                    "bsonType": "number"
                },
                "integrations": {
                    "bsonType": "object",
                    "properties": {
                        "withERP": {
                            "bsonType": "bool"
                        },
                        "with3rdPartyApp": {
                            "bsonType": "bool"
                        },
                        "with3rdPartyTelephony": {
                            "bsonType": "bool"
                        }
                    },
                    "additionalProperties": false
                },
                "statusInfo": {
                    "bsonType": "object",
                    "properties": {
                        "isActivated": {
                            "bsonType": "bool"
                        },
                        "activationDate": {
                            "bsonType": "date"
                        },
                        "deActivationDate": {
                            "bsonType": "date"
                        },
                        "creationDate": {
                            "bsonType": "date"
                        }
                    },
                    "additionalProperties": false
                },
                "chargesPerRelease": {
                    "bsonType": "object",
                    "properties": {
                        "forSMS": {
                            "bsonType": "number"
                        },
                        "forEmail": {
                            "bsonType": "number"
                        }
                    },
                    "additionalProperties": false
                },
                "clientManagerName": {
                    "bsonType": "object",
                    "additionalProperties": true,
                    "oneOf": [
                        {
                            "bsonType": "object",
                            "properties": {
                                "client1": {
                                    "bsonType": "string"
                                }
                            },
                            "additionalProperties": true
                        },
                        {
                            "bsonType": "object",
                            "properties": {
                                "client2": {
                                    "bsonType": "string"
                                }
                            },
                            "additionalProperties": true
                        }
                    ]
                }
            },
            "additionalProperties": false
        }
    },
    "validationLevel": "off",
    "validationAction": "warn"
});
```

### <a id="6fe13ff0-983e-11ec-a11a-61c866bfca96"></a>2.1.2.2 Collection **Courses**

##### 2.1.2.2.1 **Courses** Tree Diagram

![Hackolade image](static/image53.png?raw=true)

##### 2.1.2.2.2 **Courses** Properties

<table class="collection-properties-table"><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Collection name</td><td>Courses</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Database</td><td></td></tr><tr><td>Capped</td><td></td></tr><tr><td>Size</td><td></td></tr><tr><td>Max</td><td></td></tr><tr><td>Storage engine</td><td>WiredTiger</td></tr><tr><td>Config String</td><td></td></tr><tr><td>Validation level</td><td>Off</td></tr><tr><td>Validation action</td><td>Warn</td></tr><tr><td>Additional properties</td><td>false</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

##### 2.1.2.2.3 **Courses** Fields

<table><thead><tr><td>Field</td><td>Type</td><td>Req</td><td>Key</td><td>Description</td><td>Comments</td></tr></thead><tbody><tr><td><a href=#6d894200-9845-11ec-a11a-61c866bfca96 class="margin-0">courseId</a></td><td class="no-break-word">objectId</td><td>false</td><td>dk</td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#89d3d790-9845-11ec-a11a-61c866bfca96 class="margin-0">clientId</a></td><td class="no-break-word">objectId</td><td>false</td><td>fk</td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#7683d780-9845-11ec-a11a-61c866bfca96 class="margin-0">courseName</a></td><td class="no-break-word">string</td><td>false</td><td>dk</td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#ae283a00-9845-11ec-a11a-61c866bfca96 class="margin-0">courseDescription</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#cf109aa0-9845-11ec-a11a-61c866bfca96 class="margin-0">Duration</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#b7cf1510-9845-11ec-a11a-61c866bfca96 class="margin-0">fees</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#a3c69a70-9845-11ec-a11a-61c866bfca96 class="margin-0">isActivated</a></td><td class="no-break-word">boolean</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#e7d5da00-9845-11ec-a11a-61c866bfca96 class="margin-0">bannerImageUrl</a></td><td class="no-break-word">uri</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="6d894200-9845-11ec-a11a-61c866bfca96"></a>2.1.2.2.3.1 Field **courseId**

##### 2.1.2.2.3.1.1 **courseId** Tree Diagram

![Hackolade image](static/image54.png?raw=true)

##### 2.1.2.2.3.1.2 **courseId** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>courseId</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>objectId</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="89d3d790-9845-11ec-a11a-61c866bfca96"></a>2.1.2.2.3.2 Field **clientId**

##### 2.1.2.2.3.2.1 **clientId** Tree Diagram

![Hackolade image](static/image55.png?raw=true)

##### 2.1.2.2.3.2.2 **clientId** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>clientId</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>objectId</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td><a href=#28ec4d90-97e6-11ec-9947-b7f0ab1a4e72>Client</a></td></tr><tr><td>Foreign field</td><td><a href=#39b8b000-97e6-11ec-9947-b7f0ab1a4e72>client_id</a></td></tr><tr><td>Relationship type</td><td>Foreign Key</td></tr><tr><td>Relationship name</td><td>fk Client. to Courses.</td></tr><tr><td>Cardinality</td><td>n</td></tr><tr><td>Default</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="7683d780-9845-11ec-a11a-61c866bfca96"></a>2.1.2.2.3.3 Field **courseName**

##### 2.1.2.2.3.3.1 **courseName** Tree Diagram

![Hackolade image](static/image56.png?raw=true)

##### 2.1.2.2.3.3.2 **courseName** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>courseName</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td>B.Tech</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="ae283a00-9845-11ec-a11a-61c866bfca96"></a>2.1.2.2.3.4 Field **courseDescription**

##### 2.1.2.2.3.4.1 **courseDescription** Tree Diagram

![Hackolade image](static/image57.png?raw=true)

##### 2.1.2.2.3.4.2 **courseDescription** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>courseDescription</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="cf109aa0-9845-11ec-a11a-61c866bfca96"></a>2.1.2.2.3.5 Field **Duration**

##### 2.1.2.2.3.5.1 **Duration** Tree Diagram

![Hackolade image](static/image58.png?raw=true)

##### 2.1.2.2.3.5.2 **Duration** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>Duration</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td>4 years</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="b7cf1510-9845-11ec-a11a-61c866bfca96"></a>2.1.2.2.3.6 Field **fees**

##### 2.1.2.2.3.6.1 **fees** Tree Diagram

![Hackolade image](static/image59.png?raw=true)

##### 2.1.2.2.3.6.2 **fees** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>fees</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td>false</td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td>6 lacs</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="a3c69a70-9845-11ec-a11a-61c866bfca96"></a>2.1.2.2.3.7 Field **isActivated**

##### 2.1.2.2.3.7.1 **isActivated** Tree Diagram

![Hackolade image](static/image60.png?raw=true)

##### 2.1.2.2.3.7.2 **isActivated** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>isActivated</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>boolean</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Sample</td><td>true</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="e7d5da00-9845-11ec-a11a-61c866bfca96"></a>2.1.2.2.3.8 Field **bannerImageUrl**

##### 2.1.2.2.3.8.1 **bannerImageUrl** Tree Diagram

![Hackolade image](static/image61.png?raw=true)

##### 2.1.2.2.3.8.2 **bannerImageUrl** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>bannerImageUrl</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td>uri</td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

##### 2.1.2.2.4 **Courses** JSON Schema

```
{
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "title": "Courses",
    "properties": {
        "courseId": {
            "type": "string",
            "pattern": "^[a-fA-F0-9]{24}$"
        },
        "clientId": {
            "type": "string",
            "pattern": "^[a-fA-F0-9]{24}$"
        },
        "courseName": {
            "type": "string"
        },
        "courseDescription": {
            "type": "string"
        },
        "Duration": {
            "type": "string"
        },
        "fees": {
            "type": "string"
        },
        "isActivated": {
            "type": "boolean"
        },
        "bannerImageUrl": {
            "type": "string",
            "format": "uri"
        }
    },
    "additionalProperties": false
}
```

##### 2.1.2.2.5 **Courses** JSON data

```
{
    "courseId": ObjectId("507f1f77bcf86cd799439011"),
    "clientId": ObjectId("507f1f77bcf86cd799439011"),
    "courseName": "B.Tech",
    "courseDescription": "Lorem",
    "Duration": "4 years",
    "fees": "6 lacs",
    "isActivated": true,
    "bannerImageUrl": "./resource.txt#frag01"
}
```

##### 2.1.2.2.6 **Courses** Target Script

```
db.createCollection("Courses", {
    "storageEngine": {
        "wiredTiger": {}
    },
    "capped": false,
    "validator": {
        "$jsonSchema": {
            "bsonType": "object",
            "title": "Courses",
            "properties": {
                "_id": {
                    "bsonType": "objectId"
                },
                "courseId": {
                    "bsonType": "objectId"
                },
                "clientId": {
                    "bsonType": "objectId"
                },
                "courseName": {
                    "bsonType": "string"
                },
                "courseDescription": {
                    "bsonType": "string"
                },
                "Duration": {
                    "bsonType": "string"
                },
                "fees": {
                    "bsonType": "string"
                },
                "isActivated": {
                    "bsonType": "bool"
                },
                "bannerImageUrl": {
                    "bsonType": "string"
                }
            },
            "additionalProperties": false
        }
    },
    "validationLevel": "off",
    "validationAction": "warn"
});
```

### <a id="be6784d0-97db-11ec-9947-b7f0ab1a4e72"></a>2.1.2.3 Collection **Credentials**

##### 2.1.2.3.1 **Credentials** Tree Diagram

![Hackolade image](static/image62.png?raw=true)

##### 2.1.2.3.2 **Credentials** Properties

<table class="collection-properties-table"><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Collection name</td><td>Credentials</td></tr><tr><td>Technical name</td><td>Login Doc</td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Database</td><td></td></tr><tr><td>Capped</td><td></td></tr><tr><td>Size</td><td></td></tr><tr><td>Max</td><td></td></tr><tr><td>Storage engine</td><td>WiredTiger</td></tr><tr><td>Config String</td><td></td></tr><tr><td>Validation level</td><td>Off</td></tr><tr><td>Validation action</td><td>Warn</td></tr><tr><td>Additional properties</td><td>false</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

##### 2.1.2.3.3 **Credentials** Fields

<table><thead><tr><td>Field</td><td>Type</td><td>Req</td><td>Key</td><td>Description</td><td>Comments</td></tr></thead><tbody><tr><td><a href=#f93d5120-97db-11ec-9947-b7f0ab1a4e72 class="margin-0">pwd</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#e81cb430-97db-11ec-9947-b7f0ab1a4e72 class="margin-0">userName</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="f93d5120-97db-11ec-9947-b7f0ab1a4e72"></a>2.1.2.3.3.1 Field **pwd**

##### 2.1.2.3.3.1.1 **pwd** Tree Diagram

![Hackolade image](static/image63.png?raw=true)

##### 2.1.2.3.3.1.2 **pwd** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>pwd</td></tr><tr><td>Technical name</td><td>password</td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="e81cb430-97db-11ec-9947-b7f0ab1a4e72"></a>2.1.2.3.3.2 Field **userName**

##### 2.1.2.3.3.2.1 **userName** Tree Diagram

![Hackolade image](static/image64.png?raw=true)

##### 2.1.2.3.3.2.2 **userName** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>userName</td></tr><tr><td>Technical name</td><td>userName</td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

##### 2.1.2.3.4 **Credentials** JSON Schema

```
{
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "title": "Credentials",
    "properties": {
        "password": {
            "type": "string",
            "title": "pwd"
        },
        "userName": {
            "type": "string",
            "title": "userName"
        }
    },
    "additionalProperties": false
}
```

##### 2.1.2.3.5 **Credentials** JSON data

```
{
    "password": "Lorem",
    "userName": "Lorem"
}
```

##### 2.1.2.3.6 **Credentials** Target Script

```
db.createCollection("Login Doc", {
    "storageEngine": {
        "wiredTiger": {}
    },
    "capped": false,
    "validator": {
        "$jsonSchema": {
            "bsonType": "object",
            "title": "Credentials",
            "properties": {
                "_id": {
                    "bsonType": "objectId"
                },
                "password": {
                    "bsonType": "string",
                    "title": "pwd"
                },
                "userName": {
                    "bsonType": "string",
                    "title": "userName"
                }
            },
            "additionalProperties": false
        }
    },
    "validationLevel": "off",
    "validationAction": "warn"
});
```

### <a id="675aa9f0-97e6-11ec-9947-b7f0ab1a4e72"></a>2.1.2.4 Collection **Roles**

##### 2.1.2.4.1 **Roles** Tree Diagram

![Hackolade image](static/image65.png?raw=true)

##### 2.1.2.4.2 **Roles** Properties

<table class="collection-properties-table"><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Collection name</td><td>Roles</td></tr><tr><td>Technical name</td><td>userRoles</td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Database</td><td></td></tr><tr><td>Capped</td><td></td></tr><tr><td>Size</td><td></td></tr><tr><td>Max</td><td></td></tr><tr><td>Storage engine</td><td>WiredTiger</td></tr><tr><td>Config String</td><td></td></tr><tr><td>Validation level</td><td>Off</td></tr><tr><td>Validation action</td><td>Warn</td></tr><tr><td>Additional properties</td><td>true</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

##### 2.1.2.4.3 **Roles** Fields

<table><thead><tr><td>Field</td><td>Type</td><td>Req</td><td>Key</td><td>Description</td><td>Comments</td></tr></thead><tbody><tr><td><a href=#516c62e0-97e7-11ec-9947-b7f0ab1a4e72 class="margin-0">id</a></td><td class="no-break-word">objectId</td><td>false</td><td>dk</td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#c9ce41e0-97e7-11ec-9947-b7f0ab1a4e72 class="margin-0">roleName</a></td><td class="no-break-word">string</td><td>false</td><td>dk</td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="516c62e0-97e7-11ec-9947-b7f0ab1a4e72"></a>2.1.2.4.3.1 Field **id**

##### 2.1.2.4.3.1.1 **id** Tree Diagram

![Hackolade image](static/image66.png?raw=true)

##### 2.1.2.4.3.1.2 **id** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>id</td></tr><tr><td>Technical name</td><td>id</td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>objectId</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="c9ce41e0-97e7-11ec-9947-b7f0ab1a4e72"></a>2.1.2.4.3.2 Field **roleName**

##### 2.1.2.4.3.2.1 **roleName** Tree Diagram

![Hackolade image](static/image67.png?raw=true)

##### 2.1.2.4.3.2.2 **roleName** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>roleName</td></tr><tr><td>Technical name</td><td>roleName</td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td>SuperAdmin</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

##### 2.1.2.4.4 **Roles** JSON Schema

```
{
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "title": "Roles",
    "properties": {
        "id": {
            "type": "string",
            "title": "id",
            "pattern": "^[a-fA-F0-9]{24}$"
        },
        "roleName": {
            "type": "string",
            "title": "roleName"
        }
    },
    "additionalProperties": true
}
```

##### 2.1.2.4.5 **Roles** JSON data

```
{
    "id": ObjectId("507f1f77bcf86cd799439011"),
    "roleName": "SuperAdmin"
}
```

##### 2.1.2.4.6 **Roles** Target Script

```
db.createCollection("userRoles", {
    "storageEngine": {
        "wiredTiger": {}
    },
    "capped": false,
    "validator": {
        "$jsonSchema": {
            "bsonType": "object",
            "title": "Roles",
            "properties": {
                "_id": {
                    "bsonType": "objectId"
                },
                "id": {
                    "bsonType": "objectId",
                    "title": "id"
                },
                "roleName": {
                    "bsonType": "string",
                    "title": "roleName"
                }
            },
            "additionalProperties": true
        }
    },
    "validationLevel": "off",
    "validationAction": "warn"
});
```

### <a id="7be6d480-97db-11ec-9947-b7f0ab1a4e72"></a>2.1.2.5 Collection **Users**

##### 2.1.2.5.1 **Users** Tree Diagram

![Hackolade image](static/image68.png?raw=true)

##### 2.1.2.5.2 **Users** Properties

<table class="collection-properties-table"><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Collection name</td><td>Users</td></tr><tr><td>Technical name</td><td>users</td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Database</td><td></td></tr><tr><td>Capped</td><td></td></tr><tr><td>Size</td><td></td></tr><tr><td>Max</td><td></td></tr><tr><td>Storage engine</td><td>WiredTiger</td></tr><tr><td>Config String</td><td></td></tr><tr><td>Validation level</td><td>Off</td></tr><tr><td>Validation action</td><td>Warn</td></tr><tr><td>Additional properties</td><td>true</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

##### 2.1.2.5.3 **Users** Fields

<table><thead><tr><td>Field</td><td>Type</td><td>Req</td><td>Key</td><td>Description</td><td>Comments</td></tr></thead><tbody><tr><td><a href=#9ab52ec0-97db-11ec-9947-b7f0ab1a4e72 class="margin-0">userID</a></td><td class="no-break-word">objectId</td><td>false</td><td>pk</td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#a77ba3e0-97dc-11ec-9947-b7f0ab1a4e72 class="margin-0">client_id</a></td><td class="no-break-word">objectId</td><td>false</td><td>fk</td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#21e57d50-97dc-11ec-9947-b7f0ab1a4e72 class="margin-0">userName</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#bf79c2b0-97dc-11ec-9947-b7f0ab1a4e72 class="margin-0">firstName</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#cc33f840-97dc-11ec-9947-b7f0ab1a4e72 class="margin-0">middleName</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#da145e50-97dc-11ec-9947-b7f0ab1a4e72 class="margin-0">lastName</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#f4523950-97ef-11ec-8040-bdb9a5c9bfef class="margin-0">role</a></td><td class="no-break-word">document</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#f8d11870-97f4-11ec-8040-bdb9a5c9bfef class="margin-5">id</a></td><td class="no-break-word">objectId</td><td>false</td><td>fk</td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#0be4abc0-97f5-11ec-8040-bdb9a5c9bfef class="margin-5">roleName</a></td><td class="no-break-word">string</td><td>false</td><td>fk</td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#0366f1f0-97f6-11ec-8040-bdb9a5c9bfef class="margin-0">isActivated</a></td><td class="no-break-word">boolean</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#7a3ecf30-97ee-11ec-8040-bdb9a5c9bfef class="margin-0">createdAt</a></td><td class="no-break-word">date</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#3d6dd580-97f6-11ec-8040-bdb9a5c9bfef class="margin-0">lastAccessedTime</a></td><td class="no-break-word">date</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"><p>Can keep a record of last time this user performed some functions</p></div></td></tr></tbody></table>

### <a id="9ab52ec0-97db-11ec-9947-b7f0ab1a4e72"></a>2.1.2.5.3.1 Field **userID**

##### 2.1.2.5.3.1.1 **userID** Tree Diagram

![Hackolade image](static/image69.png?raw=true)

##### 2.1.2.5.3.1.2 **userID** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>userID</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>objectId</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td>true</td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="a77ba3e0-97dc-11ec-9947-b7f0ab1a4e72"></a>2.1.2.5.3.2 Field **client\_id**

##### 2.1.2.5.3.2.1 **client\_id** Tree Diagram

![Hackolade image](static/image70.png?raw=true)

##### 2.1.2.5.3.2.2 **client\_id** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>client_id</td></tr><tr><td>Technical name</td><td>Organisation ID/Client ID</td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>objectId</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td>Foreign Key</td></tr><tr><td>Relationship name</td><td>fk Client. to Users.</td></tr><tr><td>Cardinality</td><td>n</td></tr><tr><td>Default</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="21e57d50-97dc-11ec-9947-b7f0ab1a4e72"></a>2.1.2.5.3.3 Field **userName**

##### 2.1.2.5.3.3.1 **userName** Tree Diagram

![Hackolade image](static/image71.png?raw=true)

##### 2.1.2.5.3.3.2 **userName** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>userName</td></tr><tr><td>Technical name</td><td>userName</td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td>sb</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="bf79c2b0-97dc-11ec-9947-b7f0ab1a4e72"></a>2.1.2.5.3.4 Field **firstName**

##### 2.1.2.5.3.4.1 **firstName** Tree Diagram

![Hackolade image](static/image72.png?raw=true)

##### 2.1.2.5.3.4.2 **firstName** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>firstName</td></tr><tr><td>Technical name</td><td>first name</td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="cc33f840-97dc-11ec-9947-b7f0ab1a4e72"></a>2.1.2.5.3.5 Field **middleName**

##### 2.1.2.5.3.5.1 **middleName** Tree Diagram

![Hackolade image](static/image73.png?raw=true)

##### 2.1.2.5.3.5.2 **middleName** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>middleName</td></tr><tr><td>Technical name</td><td>middle name</td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="da145e50-97dc-11ec-9947-b7f0ab1a4e72"></a>2.1.2.5.3.6 Field **lastName**

##### 2.1.2.5.3.6.1 **lastName** Tree Diagram

![Hackolade image](static/image74.png?raw=true)

##### 2.1.2.5.3.6.2 **lastName** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>lastName</td></tr><tr><td>Technical name</td><td>last name</td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="f4523950-97ef-11ec-8040-bdb9a5c9bfef"></a>2.1.2.5.3.7 Field **role**

##### 2.1.2.5.3.7.1 **role** Tree Diagram

![Hackolade image](static/image75.png?raw=true)

##### 2.1.2.5.3.7.2 **role** Hierarchy

Parent field: **Users**

Child field(s):

<table class="field-properties-table"><thead><tr><td>Field</td><td>Type</td><td>Req</td><td>Key</td><td>Description</td><td>Comments</td></tr></thead><tbody><tr><td><a href=#f8d11870-97f4-11ec-8040-bdb9a5c9bfef class="margin-NaN">id</a></td><td class="no-break-word">objectId</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#0be4abc0-97f5-11ec-8040-bdb9a5c9bfef class="margin-NaN">roleName</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr></tbody></table>

##### 2.1.2.5.3.7.3 **role** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>role</td></tr><tr><td>Technical name</td><td>role</td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>document</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>DBRef</td><td></td></tr><tr><td>Min Properties</td><td></td></tr><tr><td>Max Properties</td><td></td></tr><tr><td>Additional properties</td><td>true</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="f8d11870-97f4-11ec-8040-bdb9a5c9bfef"></a>2.1.2.5.3.8 Field **id**

##### 2.1.2.5.3.8.1 **id** Tree Diagram

![Hackolade image](static/image76.png?raw=true)

##### 2.1.2.5.3.8.2 **id** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>id</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>objectId</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td>Foreign Key</td></tr><tr><td>Relationship name</td><td>fk Roles. to Users.</td></tr><tr><td>Cardinality</td><td>1</td></tr><tr><td>Default</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="0be4abc0-97f5-11ec-8040-bdb9a5c9bfef"></a>2.1.2.5.3.9 Field **roleName**

##### 2.1.2.5.3.9.1 **roleName** Tree Diagram

![Hackolade image](static/image77.png?raw=true)

##### 2.1.2.5.3.9.2 **roleName** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>roleName</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td><a href=#675aa9f0-97e6-11ec-9947-b7f0ab1a4e72>Roles</a></td></tr><tr><td>Foreign field</td><td><a href=#c9ce41e0-97e7-11ec-9947-b7f0ab1a4e72>roleName</a></td></tr><tr><td>Relationship type</td><td>Foreign Key</td></tr><tr><td>Relationship name</td><td>fk Roles. to Users.</td></tr><tr><td>Cardinality</td><td>1</td></tr><tr><td>Sample</td><td>SuperAdmin</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="0366f1f0-97f6-11ec-8040-bdb9a5c9bfef"></a>2.1.2.5.3.10 Field **isActivated**

##### 2.1.2.5.3.10.1 **isActivated** Tree Diagram

![Hackolade image](static/image78.png?raw=true)

##### 2.1.2.5.3.10.2 **isActivated** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>isActivated</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>boolean</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="7a3ecf30-97ee-11ec-8040-bdb9a5c9bfef"></a>2.1.2.5.3.11 Field **createdAt**

##### 2.1.2.5.3.11.1 **createdAt** Tree Diagram

![Hackolade image](static/image79.png?raw=true)

##### 2.1.2.5.3.11.2 **createdAt** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>createdAt</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>date</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td>false</td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Now</td><td>true</td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="3d6dd580-97f6-11ec-8040-bdb9a5c9bfef"></a>2.1.2.5.3.12 Field **lastAccessedTime**

##### 2.1.2.5.3.12.1 **lastAccessedTime** Tree Diagram

![Hackolade image](static/image80.png?raw=true)

##### 2.1.2.5.3.12.2 **lastAccessedTime** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>lastAccessedTime</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>date</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td>false</td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Now</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"><p>Can keep a record of last time this user performed some functions</p></div></td></tr></tbody></table>

##### 2.1.2.5.4 **Users** JSON Schema

```
{
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "title": "Users",
    "properties": {
        "userID": {
            "type": "string",
            "pattern": "^[a-fA-F0-9]{24}$"
        },
        "Organisation ID/Client ID": {
            "type": "string",
            "title": "client_id",
            "pattern": "^[a-fA-F0-9]{24}$"
        },
        "userName": {
            "type": "string",
            "title": "userName"
        },
        "first name": {
            "type": "string",
            "title": "firstName"
        },
        "middle name": {
            "type": "string",
            "title": "middleName"
        },
        "last name": {
            "type": "string",
            "title": "lastName"
        },
        "role": {
            "type": "object",
            "title": "role",
            "properties": {
                "id": {
                    "type": "string",
                    "pattern": "^[a-fA-F0-9]{24}$"
                },
                "roleName": {
                    "type": "string"
                }
            },
            "additionalProperties": true
        },
        "isActivated": {
            "type": "boolean"
        },
        "createdAt": {
            "type": "string",
            "format": "date-time"
        },
        "lastAccessedTime": {
            "type": "string",
            "format": "date-time"
        }
    },
    "additionalProperties": true
}
```

##### 2.1.2.5.5 **Users** JSON data

```
{
    "userID": ObjectId("507f1f77bcf86cd799439011"),
    "Organisation ID/Client ID": ObjectId("507f1f77bcf86cd799439011"),
    "userName": "sb",
    "first name": "Lorem",
    "middle name": "Lorem",
    "last name": "Lorem",
    "role": {
        "id": ObjectId("507f1f77bcf86cd799439011"),
        "roleName": "SuperAdmin"
    },
    "isActivated": true,
    "createdAt": ISODate("2016-04-08T15:06:21.595Z"),
    "lastAccessedTime": ISODate("2016-04-08T15:06:21.595Z")
}
```

##### 2.1.2.5.6 **Users** Target Script

```
db.createCollection("users", {
    "storageEngine": {
        "wiredTiger": {}
    },
    "capped": false,
    "validator": {
        "$jsonSchema": {
            "bsonType": "object",
            "title": "Users",
            "properties": {
                "_id": {
                    "bsonType": "objectId"
                },
                "userID": {
                    "bsonType": "objectId"
                },
                "Organisation ID/Client ID": {
                    "bsonType": "objectId",
                    "title": "client_id"
                },
                "userName": {
                    "bsonType": "string",
                    "title": "userName"
                },
                "first name": {
                    "bsonType": "string",
                    "title": "firstName"
                },
                "middle name": {
                    "bsonType": "string",
                    "title": "middleName"
                },
                "last name": {
                    "bsonType": "string",
                    "title": "lastName"
                },
                "role": {
                    "bsonType": "object",
                    "title": "role",
                    "properties": {
                        "id": {
                            "bsonType": "objectId"
                        },
                        "roleName": {
                            "bsonType": "string"
                        }
                    },
                    "additionalProperties": true
                },
                "isActivated": {
                    "bsonType": "bool"
                },
                "createdAt": {
                    "bsonType": "date"
                },
                "lastAccessedTime": {
                    "bsonType": "date"
                }
            },
            "additionalProperties": true
        }
    },
    "validationLevel": "off",
    "validationAction": "warn"
});
```

### <a id="01333ab0-9846-11ec-a11a-61c866bfca96"></a>2.1.2.6 Collection **specializations**

##### 2.1.2.6.1 **specializations** Tree Diagram

![Hackolade image](static/image81.png?raw=true)

##### 2.1.2.6.2 **specializations** Properties

<table class="collection-properties-table"><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Collection name</td><td>specializations</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Database</td><td></td></tr><tr><td>Capped</td><td></td></tr><tr><td>Size</td><td></td></tr><tr><td>Max</td><td></td></tr><tr><td>Storage engine</td><td>WiredTiger</td></tr><tr><td>Config String</td><td></td></tr><tr><td>Validation level</td><td>Off</td></tr><tr><td>Validation action</td><td>Warn</td></tr><tr><td>Additional properties</td><td>false</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

##### 2.1.2.6.3 **specializations** Fields

<table><thead><tr><td>Field</td><td>Type</td><td>Req</td><td>Key</td><td>Description</td><td>Comments</td></tr></thead><tbody><tr><td><a href=#142f0040-9846-11ec-a11a-61c866bfca96 class="margin-0">id</a></td><td class="no-break-word">objectId</td><td>false</td><td>dk</td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#19518bb0-9846-11ec-a11a-61c866bfca96 class="margin-0">courseId</a></td><td class="no-break-word">objectId</td><td>false</td><td>fk</td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#29e1cf80-9846-11ec-a11a-61c866bfca96 class="margin-0">name</a></td><td class="no-break-word">string</td><td>false</td><td>dk</td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#2f6fc6f0-9846-11ec-a11a-61c866bfca96 class="margin-0">description</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#3acf2770-9846-11ec-a11a-61c866bfca96 class="margin-0">isActivated</a></td><td class="no-break-word">boolean</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="142f0040-9846-11ec-a11a-61c866bfca96"></a>2.1.2.6.3.1 Field **id**

##### 2.1.2.6.3.1.1 **id** Tree Diagram

![Hackolade image](static/image82.png?raw=true)

##### 2.1.2.6.3.1.2 **id** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>id</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>objectId</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="19518bb0-9846-11ec-a11a-61c866bfca96"></a>2.1.2.6.3.2 Field **courseId**

##### 2.1.2.6.3.2.1 **courseId** Tree Diagram

![Hackolade image](static/image83.png?raw=true)

##### 2.1.2.6.3.2.2 **courseId** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>courseId</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>objectId</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td><a href=#6fe13ff0-983e-11ec-a11a-61c866bfca96>Courses</a></td></tr><tr><td>Foreign field</td><td><a href=#6d894200-9845-11ec-a11a-61c866bfca96>courseId</a></td></tr><tr><td>Relationship type</td><td>Foreign Key</td></tr><tr><td>Relationship name</td><td>fk Courses. to specializations.</td></tr><tr><td>Cardinality</td><td>n</td></tr><tr><td>Default</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="29e1cf80-9846-11ec-a11a-61c866bfca96"></a>2.1.2.6.3.3 Field **name**

##### 2.1.2.6.3.3.1 **name** Tree Diagram

![Hackolade image](static/image84.png?raw=true)

##### 2.1.2.6.3.3.2 **name** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>name</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="2f6fc6f0-9846-11ec-a11a-61c866bfca96"></a>2.1.2.6.3.4 Field **description**

##### 2.1.2.6.3.4.1 **description** Tree Diagram

![Hackolade image](static/image85.png?raw=true)

##### 2.1.2.6.3.4.2 **description** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>description</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="3acf2770-9846-11ec-a11a-61c866bfca96"></a>2.1.2.6.3.5 Field **isActivated**

##### 2.1.2.6.3.5.1 **isActivated** Tree Diagram

![Hackolade image](static/image86.png?raw=true)

##### 2.1.2.6.3.5.2 **isActivated** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>isActivated</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>boolean</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

##### 2.1.2.6.4 **specializations** JSON Schema

```
{
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "title": "specializations",
    "properties": {
        "id": {
            "type": "string",
            "pattern": "^[a-fA-F0-9]{24}$"
        },
        "courseId": {
            "type": "string",
            "pattern": "^[a-fA-F0-9]{24}$"
        },
        "name": {
            "type": "string"
        },
        "description": {
            "type": "string"
        },
        "isActivated": {
            "type": "boolean"
        }
    },
    "additionalProperties": false
}
```

##### 2.1.2.6.5 **specializations** JSON data

```
{
    "id": ObjectId("507f1f77bcf86cd799439011"),
    "courseId": ObjectId("507f1f77bcf86cd799439011"),
    "name": "Lorem",
    "description": "Lorem",
    "isActivated": true
}
```

##### 2.1.2.6.6 **specializations** Target Script

```
db.createCollection("specializations", {
    "storageEngine": {
        "wiredTiger": {}
    },
    "capped": false,
    "validator": {
        "$jsonSchema": {
            "bsonType": "object",
            "title": "specializations",
            "properties": {
                "_id": {
                    "bsonType": "objectId"
                },
                "id": {
                    "bsonType": "objectId"
                },
                "courseId": {
                    "bsonType": "objectId"
                },
                "name": {
                    "bsonType": "string"
                },
                "description": {
                    "bsonType": "string"
                },
                "isActivated": {
                    "bsonType": "bool"
                }
            },
            "additionalProperties": false
        }
    },
    "validationLevel": "off",
    "validationAction": "warn"
});
```

### <a id="86e576f0-9855-11ec-a11a-61c866bfca96"></a>2.1.2.7 Collection **studentApplicationForms**

##### 2.1.2.7.1 **studentApplicationForms** Tree Diagram

![Hackolade image](static/image87.png?raw=true)

##### 2.1.2.7.2 **studentApplicationForms** Properties

<table class="collection-properties-table"><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Collection name</td><td>studentApplicationForms</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Database</td><td></td></tr><tr><td>Capped</td><td></td></tr><tr><td>Size</td><td></td></tr><tr><td>Max</td><td></td></tr><tr><td>Storage engine</td><td>WiredTiger</td></tr><tr><td>Config String</td><td></td></tr><tr><td>Validation level</td><td>Off</td></tr><tr><td>Validation action</td><td>Warn</td></tr><tr><td>Additional properties</td><td>false</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

##### 2.1.2.7.3 **studentApplicationForms** Fields

<table><thead><tr><td>Field</td><td>Type</td><td>Req</td><td>Key</td><td>Description</td><td>Comments</td></tr></thead><tbody><tr><td><a href=#2605b2e0-98ab-11ec-a8e6-f363f79d3ea0 class="margin-0">applicationId</a></td><td class="no-break-word">objectId</td><td>false</td><td>dk</td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#2f2e8450-98ab-11ec-a8e6-f363f79d3ea0 class="margin-0">studentId</a></td><td class="no-break-word">objectId</td><td>false</td><td>fk</td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#5ee3a6d0-98ab-11ec-a8e6-f363f79d3ea0 class="margin-0">courseId</a></td><td class="no-break-word">objectId</td><td>false</td><td>fk</td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#68490f40-98af-11ec-a8e6-f363f79d3ea0 class="margin-0">specId_1</a></td><td class="no-break-word">objectId</td><td>false</td><td>fk</td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#81422fe0-98af-11ec-a8e6-f363f79d3ea0 class="margin-0">specId_2</a></td><td class="no-break-word">objectId</td><td>false</td><td>fk</td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#8dfe1320-98af-11ec-a8e6-f363f79d3ea0 class="margin-0">specId_3</a></td><td class="no-break-word">objectId</td><td>false</td><td>fk</td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#feeb8770-98af-11ec-a8e6-f363f79d3ea0 class="margin-0">payment</a></td><td class="no-break-word">document</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"><p>will add payment related info here</p></div></td></tr><tr><td><a href=#4e81acb0-98b0-11ec-a8e6-f363f79d3ea0 class="margin-0">current_stage</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"><p>can be used to define on which stage student is in application form</p></div></td></tr></tbody></table>

### <a id="2605b2e0-98ab-11ec-a8e6-f363f79d3ea0"></a>2.1.2.7.3.1 Field **applicationId**

##### 2.1.2.7.3.1.1 **applicationId** Tree Diagram

![Hackolade image](static/image88.png?raw=true)

##### 2.1.2.7.3.1.2 **applicationId** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>applicationId</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>objectId</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="2f2e8450-98ab-11ec-a8e6-f363f79d3ea0"></a>2.1.2.7.3.2 Field **studentId**

##### 2.1.2.7.3.2.1 **studentId** Tree Diagram

![Hackolade image](static/image89.png?raw=true)

##### 2.1.2.7.3.2.2 **studentId** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>studentId</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>objectId</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td><a href=#64c55110-983e-11ec-a11a-61c866bfca96>studentsPrimaryDetails</a></td></tr><tr><td>Foreign field</td><td><a href=#2b041620-984b-11ec-a11a-61c866bfca96>id</a></td></tr><tr><td>Relationship type</td><td>Foreign Key</td></tr><tr><td>Relationship name</td><td>fk studentsPrimaryDetails. to studentApplicationForms.</td></tr><tr><td>Cardinality</td><td>n</td></tr><tr><td>Default</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="5ee3a6d0-98ab-11ec-a8e6-f363f79d3ea0"></a>2.1.2.7.3.3 Field **courseId**

##### 2.1.2.7.3.3.1 **courseId** Tree Diagram

![Hackolade image](static/image90.png?raw=true)

##### 2.1.2.7.3.3.2 **courseId** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>courseId</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>objectId</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td><a href=#6fe13ff0-983e-11ec-a11a-61c866bfca96>Courses</a></td></tr><tr><td>Foreign field</td><td><a href=#6d894200-9845-11ec-a11a-61c866bfca96>courseId</a></td></tr><tr><td>Relationship type</td><td>Foreign Key</td></tr><tr><td>Relationship name</td><td>fk Courses. to studentApplicationForms.</td></tr><tr><td>Cardinality</td><td>n</td></tr><tr><td>Default</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="68490f40-98af-11ec-a8e6-f363f79d3ea0"></a>2.1.2.7.3.4 Field **specId\_1**

##### 2.1.2.7.3.4.1 **specId\_1** Tree Diagram

![Hackolade image](static/image91.png?raw=true)

##### 2.1.2.7.3.4.2 **specId\_1** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>specId_1</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>objectId</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td><a href=#01333ab0-9846-11ec-a11a-61c866bfca96>specializations</a></td></tr><tr><td>Foreign field</td><td><a href=#142f0040-9846-11ec-a11a-61c866bfca96>id</a></td></tr><tr><td>Relationship type</td><td>Foreign Key</td></tr><tr><td>Relationship name</td><td>fk specializations. to studentApplicationForms.</td></tr><tr><td>Cardinality</td><td>n</td></tr><tr><td>Default</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="81422fe0-98af-11ec-a8e6-f363f79d3ea0"></a>2.1.2.7.3.5 Field **specId\_2**

##### 2.1.2.7.3.5.1 **specId\_2** Tree Diagram

![Hackolade image](static/image92.png?raw=true)

##### 2.1.2.7.3.5.2 **specId\_2** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>specId_2</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>objectId</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td><a href=#01333ab0-9846-11ec-a11a-61c866bfca96>specializations</a></td></tr><tr><td>Foreign field</td><td><a href=#142f0040-9846-11ec-a11a-61c866bfca96>id</a></td></tr><tr><td>Relationship type</td><td>Foreign Key</td></tr><tr><td>Relationship name</td><td>fk specializations. to studentApplicationForms.</td></tr><tr><td>Cardinality</td><td>n</td></tr><tr><td>Default</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="8dfe1320-98af-11ec-a8e6-f363f79d3ea0"></a>2.1.2.7.3.6 Field **specId\_3**

##### 2.1.2.7.3.6.1 **specId\_3** Tree Diagram

![Hackolade image](static/image93.png?raw=true)

##### 2.1.2.7.3.6.2 **specId\_3** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>specId_3</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>objectId</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td><a href=#01333ab0-9846-11ec-a11a-61c866bfca96>specializations</a></td></tr><tr><td>Foreign field</td><td><a href=#142f0040-9846-11ec-a11a-61c866bfca96>id</a></td></tr><tr><td>Relationship type</td><td>Foreign Key</td></tr><tr><td>Relationship name</td><td>fk specializations. to studentApplicationForms.</td></tr><tr><td>Cardinality</td><td>n</td></tr><tr><td>Default</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="feeb8770-98af-11ec-a8e6-f363f79d3ea0"></a>2.1.2.7.3.7 Field **payment**

##### 2.1.2.7.3.7.1 **payment** Tree Diagram

![Hackolade image](static/image94.png?raw=true)

##### 2.1.2.7.3.7.2 **payment** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>payment</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>document</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>DBRef</td><td></td></tr><tr><td>Min Properties</td><td></td></tr><tr><td>Max Properties</td><td></td></tr><tr><td>Additional properties</td><td>false</td></tr><tr><td>Comments</td><td><div class="docs-markdown"><p>will add payment related info here</p></div></td></tr></tbody></table>

### <a id="4e81acb0-98b0-11ec-a8e6-f363f79d3ea0"></a>2.1.2.7.3.8 Field **current\_stage**

##### 2.1.2.7.3.8.1 **current\_stage** Tree Diagram

![Hackolade image](static/image95.png?raw=true)

##### 2.1.2.7.3.8.2 **current\_stage** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>current_stage</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"><p>can be used to define on which stage student is in application form</p></div></td></tr></tbody></table>

##### 2.1.2.7.4 **studentApplicationForms** JSON Schema

```
{
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "title": "studentApplicationForms",
    "properties": {
        "applicationId": {
            "type": "string",
            "pattern": "^[a-fA-F0-9]{24}$"
        },
        "studentId": {
            "type": "string",
            "pattern": "^[a-fA-F0-9]{24}$"
        },
        "courseId": {
            "type": "string",
            "pattern": "^[a-fA-F0-9]{24}$"
        },
        "specId_1": {
            "type": "string",
            "pattern": "^[a-fA-F0-9]{24}$"
        },
        "specId_2": {
            "type": "string",
            "pattern": "^[a-fA-F0-9]{24}$"
        },
        "specId_3": {
            "type": "string",
            "pattern": "^[a-fA-F0-9]{24}$"
        },
        "payment": {
            "type": "object",
            "additionalProperties": false
        },
        "current_stage": {
            "type": "string"
        }
    },
    "additionalProperties": false
}
```

##### 2.1.2.7.5 **studentApplicationForms** JSON data

```
{
    "applicationId": ObjectId("507f1f77bcf86cd799439011"),
    "studentId": ObjectId("507f1f77bcf86cd799439011"),
    "courseId": ObjectId("507f1f77bcf86cd799439011"),
    "specId_1": ObjectId("507f1f77bcf86cd799439011"),
    "specId_2": ObjectId("507f1f77bcf86cd799439011"),
    "specId_3": ObjectId("507f1f77bcf86cd799439011"),
    "payment": {},
    "current_stage": "Lorem"
}
```

##### 2.1.2.7.6 **studentApplicationForms** Target Script

```
db.createCollection("studentApplicationForms", {
    "storageEngine": {
        "wiredTiger": {}
    },
    "capped": false,
    "validator": {
        "$jsonSchema": {
            "bsonType": "object",
            "title": "studentApplicationForms",
            "properties": {
                "_id": {
                    "bsonType": "objectId"
                },
                "applicationId": {
                    "bsonType": "objectId"
                },
                "studentId": {
                    "bsonType": "objectId"
                },
                "courseId": {
                    "bsonType": "objectId"
                },
                "specId_1": {
                    "bsonType": "objectId"
                },
                "specId_2": {
                    "bsonType": "objectId"
                },
                "specId_3": {
                    "bsonType": "objectId"
                },
                "payment": {
                    "bsonType": "object",
                    "additionalProperties": false
                },
                "current_stage": {
                    "bsonType": "string"
                }
            },
            "additionalProperties": false
        }
    },
    "validationLevel": "off",
    "validationAction": "warn"
});
```

### <a id="d9a1d4b0-9850-11ec-a11a-61c866bfca96"></a>2.1.2.8 Collection **studentSecondaryDetails**

##### 2.1.2.8.1 **studentSecondaryDetails** Tree Diagram

![Hackolade image](static/image96.png?raw=true)

##### 2.1.2.8.2 **studentSecondaryDetails** Properties

<table class="collection-properties-table"><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Collection name</td><td>studentSecondaryDetails</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Database</td><td></td></tr><tr><td>Capped</td><td></td></tr><tr><td>Size</td><td></td></tr><tr><td>Max</td><td></td></tr><tr><td>Storage engine</td><td>WiredTiger</td></tr><tr><td>Config String</td><td></td></tr><tr><td>Validation level</td><td>Off</td></tr><tr><td>Validation action</td><td>Warn</td></tr><tr><td>Additional properties</td><td>false</td></tr><tr><td>Comments</td><td><div class="docs-markdown"><p>Details that arent frequently being accessed for student will be stored here</p></div></td></tr></tbody></table>

##### 2.1.2.8.3 **studentSecondaryDetails** Fields

<table><thead><tr><td>Field</td><td>Type</td><td>Req</td><td>Key</td><td>Description</td><td>Comments</td></tr></thead><tbody><tr><td><a href=#92e38540-9851-11ec-a11a-61c866bfca96 class="margin-0">studentID</a></td><td class="no-break-word">objectId</td><td>false</td><td>fk</td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#8d6b11a0-9851-11ec-a11a-61c866bfca96 class="margin-0">educationDetails</a></td><td class="no-break-word">document</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#bcbd41b0-9853-11ec-a11a-61c866bfca96 class="margin-5">tenth_school_details</a></td><td class="no-break-word">document</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#e5161560-9853-11ec-a11a-61c866bfca96 class="margin-10">schoolName</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#eb5ef860-9853-11ec-a11a-61c866bfca96 class="margin-10">board</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#f0539600-9853-11ec-a11a-61c866bfca96 class="margin-10">yearOfPassing</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#f687b880-9853-11ec-a11a-61c866bfca96 class="margin-10">markingShceme</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#fba69a70-9853-11ec-a11a-61c866bfca96 class="margin-10">obstainedCGPA</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#11de2a10-9854-11ec-a11a-61c866bfca96 class="margin-10">schoolCode</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#1c777b70-9854-11ec-a11a-61c866bfca96 class="margin-10">tenth_subject_wise_details</a></td><td class="no-break-word">array</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#59be6ed0-9854-11ec-a11a-61c866bfca96 class="margin-15">[0]</a></td><td class="no-break-word">document</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#603e6760-9854-11ec-a11a-61c866bfca96 class="margin-20">subjectName</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#64585c70-9854-11ec-a11a-61c866bfca96 class="margin-20">subjectMarks</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#dcb68760-9853-11ec-a11a-61c866bfca96 class="margin-5">inter_school_details</a></td><td class="no-break-word">document</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#7360c7c0-9854-11ec-a11a-61c866bfca96 class="margin-10">schoolName</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#73692c30-9854-11ec-a11a-61c866bfca96 class="margin-10">board</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#736f94d0-9854-11ec-a11a-61c866bfca96 class="margin-10">yearOfPassing</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#7375af50-9854-11ec-a11a-61c866bfca96 class="margin-10">markingShceme</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#737c17f0-9854-11ec-a11a-61c866bfca96 class="margin-10">obstainedCGPA</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#7382a7a0-9854-11ec-a11a-61c866bfca96 class="margin-10">stream</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#81f19210-9854-11ec-a11a-61c866bfca96 class="margin-10">appearedForJEE</a></td><td class="no-break-word">boolean</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#8d71ef70-9851-11ec-a11a-61c866bfca96 class="margin-0">parentsDetails</a></td><td class="no-break-word">document</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#989f8a30-9854-11ec-a11a-61c866bfca96 class="margin-5">fatherDetails</a></td><td class="no-break-word">document</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#bc261550-9854-11ec-a11a-61c866bfca96 class="margin-10">salutation</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#9dacb8e0-9854-11ec-a11a-61c866bfca96 class="margin-10">name</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#a4715b90-9854-11ec-a11a-61c866bfca96 class="margin-10">emailAddress</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#ad856c80-9854-11ec-a11a-61c866bfca96 class="margin-10">mobNumber</a></td><td class="no-break-word">numeric</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#c6352810-9854-11ec-a11a-61c866bfca96 class="margin-5">motherDetails</a></td><td class="no-break-word">document</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#c6354f21-9854-11ec-a11a-61c866bfca96 class="margin-10">salutation</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#c6354f22-9854-11ec-a11a-61c866bfca96 class="margin-10">name</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#c6354f23-9854-11ec-a11a-61c866bfca96 class="margin-10">emailAddress</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#c6354f24-9854-11ec-a11a-61c866bfca96 class="margin-10">mobNumber</a></td><td class="no-break-word">numeric</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#cb9ef5b0-9854-11ec-a11a-61c866bfca96 class="margin-0">guardianDetails</a></td><td class="no-break-word">document</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#cb9f1cc0-9854-11ec-a11a-61c866bfca96 class="margin-5">salutation</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#cb9f1cc1-9854-11ec-a11a-61c866bfca96 class="margin-5">name</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#cb9f1cc2-9854-11ec-a11a-61c866bfca96 class="margin-5">emailAddress</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#cb9f1cc3-9854-11ec-a11a-61c866bfca96 class="margin-5">mobNumber</a></td><td class="no-break-word">numeric</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#de746e90-9854-11ec-a11a-61c866bfca96 class="margin-5">occupation</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#e2908680-9854-11ec-a11a-61c866bfca96 class="margin-5">designation</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#e87b9210-9854-11ec-a11a-61c866bfca96 class="margin-5">relationshipWithStudent</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#f563b570-9854-11ec-a11a-61c866bfca96 class="margin-0">familyAnnualIncome</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="92e38540-9851-11ec-a11a-61c866bfca96"></a>2.1.2.8.3.1 Field **studentID**

##### 2.1.2.8.3.1.1 **studentID** Tree Diagram

![Hackolade image](static/image97.png?raw=true)

##### 2.1.2.8.3.1.2 **studentID** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>studentID</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>objectId</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td><a href=#64c55110-983e-11ec-a11a-61c866bfca96>studentsPrimaryDetails</a></td></tr><tr><td>Foreign field</td><td><a href=#2b041620-984b-11ec-a11a-61c866bfca96>id</a></td></tr><tr><td>Relationship type</td><td>Foreign Key</td></tr><tr><td>Relationship name</td><td>fk studentsPrimaryDetails. to studentSecondaryDetails.</td></tr><tr><td>Cardinality</td><td>1</td></tr><tr><td>Default</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="8d6b11a0-9851-11ec-a11a-61c866bfca96"></a>2.1.2.8.3.2 Field **educationDetails**

##### 2.1.2.8.3.2.1 **educationDetails** Tree Diagram

![Hackolade image](static/image98.png?raw=true)

##### 2.1.2.8.3.2.2 **educationDetails** Hierarchy

Parent field: **studentSecondaryDetails**

Child field(s):

<table class="field-properties-table"><thead><tr><td>Field</td><td>Type</td><td>Req</td><td>Key</td><td>Description</td><td>Comments</td></tr></thead><tbody><tr><td><a href=#bcbd41b0-9853-11ec-a11a-61c866bfca96 class="margin-NaN">tenth_school_details</a></td><td class="no-break-word">document</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#dcb68760-9853-11ec-a11a-61c866bfca96 class="margin-NaN">inter_school_details</a></td><td class="no-break-word">document</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr></tbody></table>

##### 2.1.2.8.3.2.3 **educationDetails** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>educationDetails</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>document</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>DBRef</td><td></td></tr><tr><td>Min Properties</td><td></td></tr><tr><td>Max Properties</td><td></td></tr><tr><td>Additional properties</td><td>false</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="bcbd41b0-9853-11ec-a11a-61c866bfca96"></a>2.1.2.8.3.3 Field **tenth\_school\_details**

##### 2.1.2.8.3.3.1 **tenth\_school\_details** Tree Diagram

![Hackolade image](static/image99.png?raw=true)

##### 2.1.2.8.3.3.2 **tenth\_school\_details** Hierarchy

Parent field: **educationDetails**

Child field(s):

<table class="field-properties-table"><thead><tr><td>Field</td><td>Type</td><td>Req</td><td>Key</td><td>Description</td><td>Comments</td></tr></thead><tbody><tr><td><a href=#e5161560-9853-11ec-a11a-61c866bfca96 class="margin-NaN">schoolName</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#eb5ef860-9853-11ec-a11a-61c866bfca96 class="margin-NaN">board</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#f0539600-9853-11ec-a11a-61c866bfca96 class="margin-NaN">yearOfPassing</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#f687b880-9853-11ec-a11a-61c866bfca96 class="margin-NaN">markingShceme</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#fba69a70-9853-11ec-a11a-61c866bfca96 class="margin-NaN">obstainedCGPA</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#11de2a10-9854-11ec-a11a-61c866bfca96 class="margin-NaN">schoolCode</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#1c777b70-9854-11ec-a11a-61c866bfca96 class="margin-NaN">tenth_subject_wise_details</a></td><td class="no-break-word">array</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr></tbody></table>

##### 2.1.2.8.3.3.3 **tenth\_school\_details** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>tenth_school_details</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>document</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>DBRef</td><td></td></tr><tr><td>Min Properties</td><td></td></tr><tr><td>Max Properties</td><td></td></tr><tr><td>Additional properties</td><td>false</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="e5161560-9853-11ec-a11a-61c866bfca96"></a>2.1.2.8.3.4 Field **schoolName**

##### 2.1.2.8.3.4.1 **schoolName** Tree Diagram

![Hackolade image](static/image100.png?raw=true)

##### 2.1.2.8.3.4.2 **schoolName** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>schoolName</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td>ssps</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="eb5ef860-9853-11ec-a11a-61c866bfca96"></a>2.1.2.8.3.5 Field **board**

##### 2.1.2.8.3.5.1 **board** Tree Diagram

![Hackolade image](static/image101.png?raw=true)

##### 2.1.2.8.3.5.2 **board** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>board</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td>CBSE</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="f0539600-9853-11ec-a11a-61c866bfca96"></a>2.1.2.8.3.6 Field **yearOfPassing**

##### 2.1.2.8.3.6.1 **yearOfPassing** Tree Diagram

![Hackolade image](static/image102.png?raw=true)

##### 2.1.2.8.3.6.2 **yearOfPassing** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>yearOfPassing</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td>2021</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="f687b880-9853-11ec-a11a-61c866bfca96"></a>2.1.2.8.3.7 Field **markingShceme**

##### 2.1.2.8.3.7.1 **markingShceme** Tree Diagram

![Hackolade image](static/image103.png?raw=true)

##### 2.1.2.8.3.7.2 **markingShceme** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>markingShceme</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td>CGPA</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="fba69a70-9853-11ec-a11a-61c866bfca96"></a>2.1.2.8.3.8 Field **obstainedCGPA**

##### 2.1.2.8.3.8.1 **obstainedCGPA** Tree Diagram

![Hackolade image](static/image104.png?raw=true)

##### 2.1.2.8.3.8.2 **obstainedCGPA** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>obstainedCGPA</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td>9</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="11de2a10-9854-11ec-a11a-61c866bfca96"></a>2.1.2.8.3.9 Field **schoolCode**

##### 2.1.2.8.3.9.1 **schoolCode** Tree Diagram

![Hackolade image](static/image105.png?raw=true)

##### 2.1.2.8.3.9.2 **schoolCode** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>schoolCode</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td>123345</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="1c777b70-9854-11ec-a11a-61c866bfca96"></a>2.1.2.8.3.10 Field **tenth\_subject\_wise\_details**

##### 2.1.2.8.3.10.1 **tenth\_subject\_wise\_details** Tree Diagram

![Hackolade image](static/image106.png?raw=true)

##### 2.1.2.8.3.10.2 **tenth\_subject\_wise\_details** Hierarchy

Parent field: **tenth\_school\_details**

Child field(s):

<table class="field-properties-table"><thead><tr><td>Field</td><td>Type</td><td>Req</td><td>Key</td><td>Description</td><td>Comments</td></tr></thead><tbody><tr><td><a href=#59be6ed0-9854-11ec-a11a-61c866bfca96 class="margin-NaN">[0]</a></td><td class="no-break-word">document</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr></tbody></table>

##### 2.1.2.8.3.10.3 **tenth\_subject\_wise\_details** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>tenth_subject_wise_details</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>array</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Min items</td><td></td></tr><tr><td>Max items</td><td></td></tr><tr><td>Unique items</td><td></td></tr><tr><td>Additional items</td><td>true</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="59be6ed0-9854-11ec-a11a-61c866bfca96"></a>2.1.2.8.3.11 Field **\[0\]**

##### 2.1.2.8.3.11.1 **\[0\]** Tree Diagram

![Hackolade image](static/image107.png?raw=true)

##### 2.1.2.8.3.11.2 **\[0\]** Hierarchy

Parent field: **tenth\_subject\_wise\_details**

Child field(s):

<table class="field-properties-table"><thead><tr><td>Field</td><td>Type</td><td>Req</td><td>Key</td><td>Description</td><td>Comments</td></tr></thead><tbody><tr><td><a href=#603e6760-9854-11ec-a11a-61c866bfca96 class="margin-NaN">subjectName</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#64585c70-9854-11ec-a11a-61c866bfca96 class="margin-NaN">subjectMarks</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr></tbody></table>

##### 2.1.2.8.3.11.3 **\[0\]** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Display name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>document</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>DBRef</td><td></td></tr><tr><td>Min Properties</td><td></td></tr><tr><td>Max Properties</td><td></td></tr><tr><td>Additional properties</td><td>false</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="603e6760-9854-11ec-a11a-61c866bfca96"></a>2.1.2.8.3.12 Field **subjectName**

##### 2.1.2.8.3.12.1 **subjectName** Tree Diagram

![Hackolade image](static/image108.png?raw=true)

##### 2.1.2.8.3.12.2 **subjectName** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>subjectName</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="64585c70-9854-11ec-a11a-61c866bfca96"></a>2.1.2.8.3.13 Field **subjectMarks**

##### 2.1.2.8.3.13.1 **subjectMarks** Tree Diagram

![Hackolade image](static/image109.png?raw=true)

##### 2.1.2.8.3.13.2 **subjectMarks** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>subjectMarks</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="dcb68760-9853-11ec-a11a-61c866bfca96"></a>2.1.2.8.3.14 Field **inter\_school\_details**

##### 2.1.2.8.3.14.1 **inter\_school\_details** Tree Diagram

![Hackolade image](static/image110.png?raw=true)

##### 2.1.2.8.3.14.2 **inter\_school\_details** Hierarchy

Parent field: **educationDetails**

Child field(s):

<table class="field-properties-table"><thead><tr><td>Field</td><td>Type</td><td>Req</td><td>Key</td><td>Description</td><td>Comments</td></tr></thead><tbody><tr><td><a href=#7360c7c0-9854-11ec-a11a-61c866bfca96 class="margin-NaN">schoolName</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#73692c30-9854-11ec-a11a-61c866bfca96 class="margin-NaN">board</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#736f94d0-9854-11ec-a11a-61c866bfca96 class="margin-NaN">yearOfPassing</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#7375af50-9854-11ec-a11a-61c866bfca96 class="margin-NaN">markingShceme</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#737c17f0-9854-11ec-a11a-61c866bfca96 class="margin-NaN">obstainedCGPA</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#7382a7a0-9854-11ec-a11a-61c866bfca96 class="margin-NaN">stream</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#81f19210-9854-11ec-a11a-61c866bfca96 class="margin-NaN">appearedForJEE</a></td><td class="no-break-word">boolean</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr></tbody></table>

##### 2.1.2.8.3.14.3 **inter\_school\_details** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>inter_school_details</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>document</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>DBRef</td><td></td></tr><tr><td>Min Properties</td><td></td></tr><tr><td>Max Properties</td><td></td></tr><tr><td>Additional properties</td><td>false</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="7360c7c0-9854-11ec-a11a-61c866bfca96"></a>2.1.2.8.3.15 Field **schoolName**

##### 2.1.2.8.3.15.1 **schoolName** Tree Diagram

![Hackolade image](static/image111.png?raw=true)

##### 2.1.2.8.3.15.2 **schoolName** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>schoolName</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td>ssps</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="73692c30-9854-11ec-a11a-61c866bfca96"></a>2.1.2.8.3.16 Field **board**

##### 2.1.2.8.3.16.1 **board** Tree Diagram

![Hackolade image](static/image112.png?raw=true)

##### 2.1.2.8.3.16.2 **board** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>board</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td>CBSE</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="736f94d0-9854-11ec-a11a-61c866bfca96"></a>2.1.2.8.3.17 Field **yearOfPassing**

##### 2.1.2.8.3.17.1 **yearOfPassing** Tree Diagram

![Hackolade image](static/image113.png?raw=true)

##### 2.1.2.8.3.17.2 **yearOfPassing** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>yearOfPassing</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td>2021</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="7375af50-9854-11ec-a11a-61c866bfca96"></a>2.1.2.8.3.18 Field **markingShceme**

##### 2.1.2.8.3.18.1 **markingShceme** Tree Diagram

![Hackolade image](static/image114.png?raw=true)

##### 2.1.2.8.3.18.2 **markingShceme** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>markingShceme</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td>CGPA</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="737c17f0-9854-11ec-a11a-61c866bfca96"></a>2.1.2.8.3.19 Field **obstainedCGPA**

##### 2.1.2.8.3.19.1 **obstainedCGPA** Tree Diagram

![Hackolade image](static/image115.png?raw=true)

##### 2.1.2.8.3.19.2 **obstainedCGPA** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>obstainedCGPA</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td>9</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="7382a7a0-9854-11ec-a11a-61c866bfca96"></a>2.1.2.8.3.20 Field **stream**

##### 2.1.2.8.3.20.1 **stream** Tree Diagram

![Hackolade image](static/image116.png?raw=true)

##### 2.1.2.8.3.20.2 **stream** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>stream</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td>123345</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="81f19210-9854-11ec-a11a-61c866bfca96"></a>2.1.2.8.3.21 Field **appearedForJEE**

##### 2.1.2.8.3.21.1 **appearedForJEE** Tree Diagram

![Hackolade image](static/image117.png?raw=true)

##### 2.1.2.8.3.21.2 **appearedForJEE** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>appearedForJEE</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>boolean</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="8d71ef70-9851-11ec-a11a-61c866bfca96"></a>2.1.2.8.3.22 Field **parentsDetails**

##### 2.1.2.8.3.22.1 **parentsDetails** Tree Diagram

![Hackolade image](static/image118.png?raw=true)

##### 2.1.2.8.3.22.2 **parentsDetails** Hierarchy

Parent field: **studentSecondaryDetails**

Child field(s):

<table class="field-properties-table"><thead><tr><td>Field</td><td>Type</td><td>Req</td><td>Key</td><td>Description</td><td>Comments</td></tr></thead><tbody><tr><td><a href=#989f8a30-9854-11ec-a11a-61c866bfca96 class="margin-NaN">fatherDetails</a></td><td class="no-break-word">document</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#c6352810-9854-11ec-a11a-61c866bfca96 class="margin-NaN">motherDetails</a></td><td class="no-break-word">document</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr></tbody></table>

##### 2.1.2.8.3.22.3 **parentsDetails** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>parentsDetails</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>document</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>DBRef</td><td></td></tr><tr><td>Min Properties</td><td></td></tr><tr><td>Max Properties</td><td></td></tr><tr><td>Additional properties</td><td>false</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="989f8a30-9854-11ec-a11a-61c866bfca96"></a>2.1.2.8.3.23 Field **fatherDetails**

##### 2.1.2.8.3.23.1 **fatherDetails** Tree Diagram

![Hackolade image](static/image119.png?raw=true)

##### 2.1.2.8.3.23.2 **fatherDetails** Hierarchy

Parent field: **parentsDetails**

Child field(s):

<table class="field-properties-table"><thead><tr><td>Field</td><td>Type</td><td>Req</td><td>Key</td><td>Description</td><td>Comments</td></tr></thead><tbody><tr><td><a href=#bc261550-9854-11ec-a11a-61c866bfca96 class="margin-NaN">salutation</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#9dacb8e0-9854-11ec-a11a-61c866bfca96 class="margin-NaN">name</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#a4715b90-9854-11ec-a11a-61c866bfca96 class="margin-NaN">emailAddress</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#ad856c80-9854-11ec-a11a-61c866bfca96 class="margin-NaN">mobNumber</a></td><td class="no-break-word">numeric</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr></tbody></table>

##### 2.1.2.8.3.23.3 **fatherDetails** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>fatherDetails</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>document</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>DBRef</td><td></td></tr><tr><td>Min Properties</td><td></td></tr><tr><td>Max Properties</td><td></td></tr><tr><td>Additional properties</td><td>false</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="bc261550-9854-11ec-a11a-61c866bfca96"></a>2.1.2.8.3.24 Field **salutation**

##### 2.1.2.8.3.24.1 **salutation** Tree Diagram

![Hackolade image](static/image120.png?raw=true)

##### 2.1.2.8.3.24.2 **salutation** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>salutation</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="9dacb8e0-9854-11ec-a11a-61c866bfca96"></a>2.1.2.8.3.25 Field **name**

##### 2.1.2.8.3.25.1 **name** Tree Diagram

![Hackolade image](static/image121.png?raw=true)

##### 2.1.2.8.3.25.2 **name** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>name</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td>ABCD</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="a4715b90-9854-11ec-a11a-61c866bfca96"></a>2.1.2.8.3.26 Field **emailAddress**

##### 2.1.2.8.3.26.1 **emailAddress** Tree Diagram

![Hackolade image](static/image122.png?raw=true)

##### 2.1.2.8.3.26.2 **emailAddress** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>emailAddress</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td>abcd@XYZ.COM</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="ad856c80-9854-11ec-a11a-61c866bfca96"></a>2.1.2.8.3.27 Field **mobNumber**

##### 2.1.2.8.3.27.1 **mobNumber** Tree Diagram

![Hackolade image](static/image123.png?raw=true)

##### 2.1.2.8.3.27.2 **mobNumber** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>mobNumber</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>numeric</td></tr><tr><td>Subtype</td><td></td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Unit</td><td></td></tr><tr><td>Min value</td><td></td></tr><tr><td>Excl min</td><td></td></tr><tr><td>Max value</td><td></td></tr><tr><td>Excl max</td><td></td></tr><tr><td>Multiple of</td><td></td></tr><tr><td>Divisible by</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Sample</td><td>1234567</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="c6352810-9854-11ec-a11a-61c866bfca96"></a>2.1.2.8.3.28 Field **motherDetails**

##### 2.1.2.8.3.28.1 **motherDetails** Tree Diagram

![Hackolade image](static/image124.png?raw=true)

##### 2.1.2.8.3.28.2 **motherDetails** Hierarchy

Parent field: **parentsDetails**

Child field(s):

<table class="field-properties-table"><thead><tr><td>Field</td><td>Type</td><td>Req</td><td>Key</td><td>Description</td><td>Comments</td></tr></thead><tbody><tr><td><a href=#c6354f21-9854-11ec-a11a-61c866bfca96 class="margin-NaN">salutation</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#c6354f22-9854-11ec-a11a-61c866bfca96 class="margin-NaN">name</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#c6354f23-9854-11ec-a11a-61c866bfca96 class="margin-NaN">emailAddress</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#c6354f24-9854-11ec-a11a-61c866bfca96 class="margin-NaN">mobNumber</a></td><td class="no-break-word">numeric</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr></tbody></table>

##### 2.1.2.8.3.28.3 **motherDetails** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>motherDetails</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>document</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>DBRef</td><td></td></tr><tr><td>Min Properties</td><td></td></tr><tr><td>Max Properties</td><td></td></tr><tr><td>Additional properties</td><td>false</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="c6354f21-9854-11ec-a11a-61c866bfca96"></a>2.1.2.8.3.29 Field **salutation**

##### 2.1.2.8.3.29.1 **salutation** Tree Diagram

![Hackolade image](static/image125.png?raw=true)

##### 2.1.2.8.3.29.2 **salutation** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>salutation</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="c6354f22-9854-11ec-a11a-61c866bfca96"></a>2.1.2.8.3.30 Field **name**

##### 2.1.2.8.3.30.1 **name** Tree Diagram

![Hackolade image](static/image126.png?raw=true)

##### 2.1.2.8.3.30.2 **name** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>name</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td>ABCD</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="c6354f23-9854-11ec-a11a-61c866bfca96"></a>2.1.2.8.3.31 Field **emailAddress**

##### 2.1.2.8.3.31.1 **emailAddress** Tree Diagram

![Hackolade image](static/image127.png?raw=true)

##### 2.1.2.8.3.31.2 **emailAddress** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>emailAddress</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td>abcd@XYZ.COM</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="c6354f24-9854-11ec-a11a-61c866bfca96"></a>2.1.2.8.3.32 Field **mobNumber**

##### 2.1.2.8.3.32.1 **mobNumber** Tree Diagram

![Hackolade image](static/image128.png?raw=true)

##### 2.1.2.8.3.32.2 **mobNumber** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>mobNumber</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>numeric</td></tr><tr><td>Subtype</td><td></td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Unit</td><td></td></tr><tr><td>Min value</td><td></td></tr><tr><td>Excl min</td><td></td></tr><tr><td>Max value</td><td></td></tr><tr><td>Excl max</td><td></td></tr><tr><td>Multiple of</td><td></td></tr><tr><td>Divisible by</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Sample</td><td>1234567</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="cb9ef5b0-9854-11ec-a11a-61c866bfca96"></a>2.1.2.8.3.33 Field **guardianDetails**

##### 2.1.2.8.3.33.1 **guardianDetails** Tree Diagram

![Hackolade image](static/image129.png?raw=true)

##### 2.1.2.8.3.33.2 **guardianDetails** Hierarchy

Parent field: **studentSecondaryDetails**

Child field(s):

<table class="field-properties-table"><thead><tr><td>Field</td><td>Type</td><td>Req</td><td>Key</td><td>Description</td><td>Comments</td></tr></thead><tbody><tr><td><a href=#cb9f1cc0-9854-11ec-a11a-61c866bfca96 class="margin-NaN">salutation</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#cb9f1cc1-9854-11ec-a11a-61c866bfca96 class="margin-NaN">name</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#cb9f1cc2-9854-11ec-a11a-61c866bfca96 class="margin-NaN">emailAddress</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#cb9f1cc3-9854-11ec-a11a-61c866bfca96 class="margin-NaN">mobNumber</a></td><td class="no-break-word">numeric</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#de746e90-9854-11ec-a11a-61c866bfca96 class="margin-NaN">occupation</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#e2908680-9854-11ec-a11a-61c866bfca96 class="margin-NaN">designation</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#e87b9210-9854-11ec-a11a-61c866bfca96 class="margin-NaN">relationshipWithStudent</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr></tbody></table>

##### 2.1.2.8.3.33.3 **guardianDetails** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>guardianDetails</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>document</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>DBRef</td><td></td></tr><tr><td>Min Properties</td><td></td></tr><tr><td>Max Properties</td><td></td></tr><tr><td>Additional properties</td><td>false</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="cb9f1cc0-9854-11ec-a11a-61c866bfca96"></a>2.1.2.8.3.34 Field **salutation**

##### 2.1.2.8.3.34.1 **salutation** Tree Diagram

![Hackolade image](static/image130.png?raw=true)

##### 2.1.2.8.3.34.2 **salutation** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>salutation</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="cb9f1cc1-9854-11ec-a11a-61c866bfca96"></a>2.1.2.8.3.35 Field **name**

##### 2.1.2.8.3.35.1 **name** Tree Diagram

![Hackolade image](static/image131.png?raw=true)

##### 2.1.2.8.3.35.2 **name** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>name</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td>ABCD</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="cb9f1cc2-9854-11ec-a11a-61c866bfca96"></a>2.1.2.8.3.36 Field **emailAddress**

##### 2.1.2.8.3.36.1 **emailAddress** Tree Diagram

![Hackolade image](static/image132.png?raw=true)

##### 2.1.2.8.3.36.2 **emailAddress** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>emailAddress</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td>abcd@XYZ.COM</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="cb9f1cc3-9854-11ec-a11a-61c866bfca96"></a>2.1.2.8.3.37 Field **mobNumber**

##### 2.1.2.8.3.37.1 **mobNumber** Tree Diagram

![Hackolade image](static/image133.png?raw=true)

##### 2.1.2.8.3.37.2 **mobNumber** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>mobNumber</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>numeric</td></tr><tr><td>Subtype</td><td></td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Unit</td><td></td></tr><tr><td>Min value</td><td></td></tr><tr><td>Excl min</td><td></td></tr><tr><td>Max value</td><td></td></tr><tr><td>Excl max</td><td></td></tr><tr><td>Multiple of</td><td></td></tr><tr><td>Divisible by</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Sample</td><td>1234567</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="de746e90-9854-11ec-a11a-61c866bfca96"></a>2.1.2.8.3.38 Field **occupation**

##### 2.1.2.8.3.38.1 **occupation** Tree Diagram

![Hackolade image](static/image134.png?raw=true)

##### 2.1.2.8.3.38.2 **occupation** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>occupation</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="e2908680-9854-11ec-a11a-61c866bfca96"></a>2.1.2.8.3.39 Field **designation**

##### 2.1.2.8.3.39.1 **designation** Tree Diagram

![Hackolade image](static/image135.png?raw=true)

##### 2.1.2.8.3.39.2 **designation** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>designation</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="e87b9210-9854-11ec-a11a-61c866bfca96"></a>2.1.2.8.3.40 Field **relationshipWithStudent**

##### 2.1.2.8.3.40.1 **relationshipWithStudent** Tree Diagram

![Hackolade image](static/image136.png?raw=true)

##### 2.1.2.8.3.40.2 **relationshipWithStudent** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>relationshipWithStudent</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="f563b570-9854-11ec-a11a-61c866bfca96"></a>2.1.2.8.3.41 Field **familyAnnualIncome**

##### 2.1.2.8.3.41.1 **familyAnnualIncome** Tree Diagram

![Hackolade image](static/image137.png?raw=true)

##### 2.1.2.8.3.41.2 **familyAnnualIncome** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>familyAnnualIncome</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td>20 lakh</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

##### 2.1.2.8.4 **studentSecondaryDetails** JSON Schema

```
{
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "title": "studentSecondaryDetails",
    "properties": {
        "studentID": {
            "type": "string",
            "pattern": "^[a-fA-F0-9]{24}$"
        },
        "educationDetails": {
            "type": "object",
            "properties": {
                "tenth_school_details": {
                    "type": "object",
                    "properties": {
                        "schoolName": {
                            "type": "string"
                        },
                        "board": {
                            "type": "string"
                        },
                        "yearOfPassing": {
                            "type": "string"
                        },
                        "markingShceme": {
                            "type": "string"
                        },
                        "obstainedCGPA": {
                            "type": "string"
                        },
                        "schoolCode": {
                            "type": "string"
                        },
                        "tenth_subject_wise_details": {
                            "type": "array",
                            "additionalItems": true,
                            "items": {
                                "type": "object",
                                "properties": {
                                    "subjectName": {
                                        "type": "string"
                                    },
                                    "subjectMarks": {
                                        "type": "string"
                                    }
                                },
                                "additionalProperties": false
                            }
                        }
                    },
                    "additionalProperties": false
                },
                "inter_school_details": {
                    "type": "object",
                    "properties": {
                        "schoolName": {
                            "type": "string"
                        },
                        "board": {
                            "type": "string"
                        },
                        "yearOfPassing": {
                            "type": "string"
                        },
                        "markingShceme": {
                            "type": "string"
                        },
                        "obstainedCGPA": {
                            "type": "string"
                        },
                        "stream": {
                            "type": "string"
                        },
                        "appearedForJEE": {
                            "type": "boolean"
                        }
                    },
                    "additionalProperties": false
                }
            },
            "additionalProperties": false
        },
        "parentsDetails": {
            "type": "object",
            "properties": {
                "fatherDetails": {
                    "type": "object",
                    "properties": {
                        "salutation": {
                            "type": "string"
                        },
                        "name": {
                            "type": "string"
                        },
                        "emailAddress": {
                            "type": "string"
                        },
                        "mobNumber": {
                            "type": "number"
                        }
                    },
                    "additionalProperties": false
                },
                "motherDetails": {
                    "type": "object",
                    "properties": {
                        "salutation": {
                            "type": "string"
                        },
                        "name": {
                            "type": "string"
                        },
                        "emailAddress": {
                            "type": "string"
                        },
                        "mobNumber": {
                            "type": "number"
                        }
                    },
                    "additionalProperties": false
                }
            },
            "additionalProperties": false
        },
        "guardianDetails": {
            "type": "object",
            "properties": {
                "salutation": {
                    "type": "string"
                },
                "name": {
                    "type": "string"
                },
                "emailAddress": {
                    "type": "string"
                },
                "mobNumber": {
                    "type": "number"
                },
                "occupation": {
                    "type": "string"
                },
                "designation": {
                    "type": "string"
                },
                "relationshipWithStudent": {
                    "type": "string"
                }
            },
            "additionalProperties": false
        },
        "familyAnnualIncome": {
            "type": "string"
        }
    },
    "additionalProperties": false
}
```

##### 2.1.2.8.5 **studentSecondaryDetails** JSON data

```
{
    "studentID": ObjectId("507f1f77bcf86cd799439011"),
    "educationDetails": {
        "tenth_school_details": {
            "schoolName": "ssps",
            "board": "CBSE",
            "yearOfPassing": "2021",
            "markingShceme": "CGPA",
            "obstainedCGPA": "9",
            "schoolCode": "123345",
            "tenth_subject_wise_details": [
                {
                    "subjectName": "Lorem",
                    "subjectMarks": "Lorem"
                }
            ]
        },
        "inter_school_details": {
            "schoolName": "ssps",
            "board": "CBSE",
            "yearOfPassing": "2021",
            "markingShceme": "CGPA",
            "obstainedCGPA": "9",
            "stream": "123345",
            "appearedForJEE": true
        }
    },
    "parentsDetails": {
        "fatherDetails": {
            "salutation": "Lorem",
            "name": "ABCD",
            "emailAddress": "abcd@XYZ.COM",
            "mobNumber": 1234567
        },
        "motherDetails": {
            "salutation": "Lorem",
            "name": "ABCD",
            "emailAddress": "abcd@XYZ.COM",
            "mobNumber": 1234567
        }
    },
    "guardianDetails": {
        "salutation": "Lorem",
        "name": "ABCD",
        "emailAddress": "abcd@XYZ.COM",
        "mobNumber": 1234567,
        "occupation": "Lorem",
        "designation": "Lorem",
        "relationshipWithStudent": "Lorem"
    },
    "familyAnnualIncome": "20 lakh"
}
```

##### 2.1.2.8.6 **studentSecondaryDetails** Target Script

```
db.createCollection("studentSecondaryDetails", {
    "storageEngine": {
        "wiredTiger": {}
    },
    "capped": false,
    "validator": {
        "$jsonSchema": {
            "bsonType": "object",
            "title": "studentSecondaryDetails",
            "properties": {
                "_id": {
                    "bsonType": "objectId"
                },
                "studentID": {
                    "bsonType": "objectId"
                },
                "educationDetails": {
                    "bsonType": "object",
                    "properties": {
                        "tenth_school_details": {
                            "bsonType": "object",
                            "properties": {
                                "schoolName": {
                                    "bsonType": "string"
                                },
                                "board": {
                                    "bsonType": "string"
                                },
                                "yearOfPassing": {
                                    "bsonType": "string"
                                },
                                "markingShceme": {
                                    "bsonType": "string"
                                },
                                "obstainedCGPA": {
                                    "bsonType": "string"
                                },
                                "schoolCode": {
                                    "bsonType": "string"
                                },
                                "tenth_subject_wise_details": {
                                    "bsonType": "array",
                                    "additionalItems": true,
                                    "items": {
                                        "bsonType": "object",
                                        "properties": {
                                            "subjectName": {
                                                "bsonType": "string"
                                            },
                                            "subjectMarks": {
                                                "bsonType": "string"
                                            }
                                        },
                                        "additionalProperties": false
                                    }
                                }
                            },
                            "additionalProperties": false
                        },
                        "inter_school_details": {
                            "bsonType": "object",
                            "properties": {
                                "schoolName": {
                                    "bsonType": "string"
                                },
                                "board": {
                                    "bsonType": "string"
                                },
                                "yearOfPassing": {
                                    "bsonType": "string"
                                },
                                "markingShceme": {
                                    "bsonType": "string"
                                },
                                "obstainedCGPA": {
                                    "bsonType": "string"
                                },
                                "stream": {
                                    "bsonType": "string"
                                },
                                "appearedForJEE": {
                                    "bsonType": "bool"
                                }
                            },
                            "additionalProperties": false
                        }
                    },
                    "additionalProperties": false
                },
                "parentsDetails": {
                    "bsonType": "object",
                    "properties": {
                        "fatherDetails": {
                            "bsonType": "object",
                            "properties": {
                                "salutation": {
                                    "bsonType": "string"
                                },
                                "name": {
                                    "bsonType": "string"
                                },
                                "emailAddress": {
                                    "bsonType": "string"
                                },
                                "mobNumber": {
                                    "bsonType": "number"
                                }
                            },
                            "additionalProperties": false
                        },
                        "motherDetails": {
                            "bsonType": "object",
                            "properties": {
                                "salutation": {
                                    "bsonType": "string"
                                },
                                "name": {
                                    "bsonType": "string"
                                },
                                "emailAddress": {
                                    "bsonType": "string"
                                },
                                "mobNumber": {
                                    "bsonType": "number"
                                }
                            },
                            "additionalProperties": false
                        }
                    },
                    "additionalProperties": false
                },
                "guardianDetails": {
                    "bsonType": "object",
                    "properties": {
                        "salutation": {
                            "bsonType": "string"
                        },
                        "name": {
                            "bsonType": "string"
                        },
                        "emailAddress": {
                            "bsonType": "string"
                        },
                        "mobNumber": {
                            "bsonType": "number"
                        },
                        "occupation": {
                            "bsonType": "string"
                        },
                        "designation": {
                            "bsonType": "string"
                        },
                        "relationshipWithStudent": {
                            "bsonType": "string"
                        }
                    },
                    "additionalProperties": false
                },
                "familyAnnualIncome": {
                    "bsonType": "string"
                }
            },
            "additionalProperties": false
        }
    },
    "validationLevel": "off",
    "validationAction": "warn"
});
```

### <a id="64c55110-983e-11ec-a11a-61c866bfca96"></a>2.1.2.9 Collection **studentsPrimaryDetails**

##### 2.1.2.9.1 **studentsPrimaryDetails** Tree Diagram

![Hackolade image](static/image138.png?raw=true)

##### 2.1.2.9.2 **studentsPrimaryDetails** Properties

<table class="collection-properties-table"><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Collection name</td><td>studentsPrimaryDetails</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Database</td><td></td></tr><tr><td>Capped</td><td></td></tr><tr><td>Size</td><td></td></tr><tr><td>Max</td><td></td></tr><tr><td>Storage engine</td><td>WiredTiger</td></tr><tr><td>Config String</td><td></td></tr><tr><td>Validation level</td><td>Off</td></tr><tr><td>Validation action</td><td>Warn</td></tr><tr><td>Additional properties</td><td>false</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

##### 2.1.2.9.3 **studentsPrimaryDetails** Fields

<table><thead><tr><td>Field</td><td>Type</td><td>Req</td><td>Key</td><td>Description</td><td>Comments</td></tr></thead><tbody><tr><td><a href=#2b041620-984b-11ec-a11a-61c866bfca96 class="margin-0">id</a></td><td class="no-break-word">objectId</td><td>false</td><td>dk</td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#2b0cc8b0-984b-11ec-a11a-61c866bfca96 class="margin-0">userName</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#c539b870-9851-11ec-a11a-61c866bfca96 class="margin-0">pwd</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#65e7a140-984f-11ec-a11a-61c866bfca96 class="margin-0">basicDetails</a></td><td class="no-break-word">document</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#9ed350d0-984f-11ec-a11a-61c866bfca96 class="margin-5">email</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#cecde0c0-984f-11ec-a11a-61c866bfca96 class="margin-5">firstName</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#d073efa0-984f-11ec-a11a-61c866bfca96 class="margin-5">middleName</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#d25cfaf0-984f-11ec-a11a-61c866bfca96 class="margin-5">lastName</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#e6cce9f0-984f-11ec-a11a-61c866bfca96 class="margin-5">nationality</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#f5053400-984f-11ec-a11a-61c866bfca96 class="margin-5">mob</a></td><td class="no-break-word">numeric</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#fb44a120-984f-11ec-a11a-61c866bfca96 class="margin-5">DOB</a></td><td class="no-break-word">date</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#032a9250-9850-11ec-a11a-61c866bfca96 class="margin-5">gender</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"><p>MALE/FEMALE/TRANS</p></div></td></tr><tr><td><a href=#0aeccee0-9850-11ec-a11a-61c866bfca96 class="margin-5">category</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#157be710-9850-11ec-a11a-61c866bfca96 class="margin-5">para-ability</a></td><td class="no-break-word">document</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"><p>is student suffers from any disability</p></div></td></tr><tr><td><a href=#34a6b930-9850-11ec-a11a-61c866bfca96 class="margin-10">isDisable</a></td><td class="no-break-word">boolean</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#4422cde0-9850-11ec-a11a-61c866bfca96 class="margin-10">nameOfDisability</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#6d5970b0-984b-11ec-a11a-61c866bfca96 class="margin-0">addressDetails</a></td><td class="no-break-word">document</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#727d34a0-984b-11ec-a11a-61c866bfca96 class="margin-5">city</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#7832b140-984b-11ec-a11a-61c866bfca96 class="margin-5">state</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#7b144d60-984b-11ec-a11a-61c866bfca96 class="margin-5">country</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#18d38870-984e-11ec-a11a-61c866bfca96 class="margin-0">courseDetails</a></td><td class="no-break-word">array</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"><p>array size cannot be more than 3</p></div></td></tr><tr><td><a href=#18d8b890-984e-11ec-a11a-61c866bfca96 class="margin-5">[0]&nbsp;courseInfo</a></td><td class="no-break-word">document</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#3afc3140-984e-11ec-a11a-61c866bfca96 class="margin-10">courseId</a></td><td class="no-break-word">objectId</td><td>false</td><td>fk</td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#3b0950a0-984e-11ec-a11a-61c866bfca96 class="margin-10">courseName</a></td><td class="no-break-word">string</td><td>false</td><td>fk</td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#fc955980-984e-11ec-a11a-61c866bfca96 class="margin-10">applicationID</a></td><td class="no-break-word">objectId</td><td>false</td><td>fk</td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#08231d00-984f-11ec-a11a-61c866bfca96 class="margin-10">status</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"><p>student is enrolled or payment is due</p></div></td></tr><tr><td><a href=#bd1eb4e0-984e-11ec-a11a-61c866bfca96 class="margin-10">specs</a></td><td class="no-break-word">array</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#bd243320-984e-11ec-a11a-61c866bfca96 class="margin-15">[0]</a></td><td class="no-break-word">document</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#c9ce3c10-984e-11ec-a11a-61c866bfca96 class="margin-20">specId</a></td><td class="no-break-word">objectId</td><td>false</td><td>fk</td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#c9da7110-984e-11ec-a11a-61c866bfca96 class="margin-20">specName</a></td><td class="no-break-word">string</td><td>false</td><td>fk</td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="2b041620-984b-11ec-a11a-61c866bfca96"></a>2.1.2.9.3.1 Field **id**

##### 2.1.2.9.3.1.1 **id** Tree Diagram

![Hackolade image](static/image139.png?raw=true)

##### 2.1.2.9.3.1.2 **id** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>id</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>objectId</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="2b0cc8b0-984b-11ec-a11a-61c866bfca96"></a>2.1.2.9.3.2 Field **userName**

##### 2.1.2.9.3.2.1 **userName** Tree Diagram

![Hackolade image](static/image140.png?raw=true)

##### 2.1.2.9.3.2.2 **userName** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>userName</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="c539b870-9851-11ec-a11a-61c866bfca96"></a>2.1.2.9.3.3 Field **pwd**

##### 2.1.2.9.3.3.1 **pwd** Tree Diagram

![Hackolade image](static/image141.png?raw=true)

##### 2.1.2.9.3.3.2 **pwd** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>pwd</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="65e7a140-984f-11ec-a11a-61c866bfca96"></a>2.1.2.9.3.4 Field **basicDetails**

##### 2.1.2.9.3.4.1 **basicDetails** Tree Diagram

![Hackolade image](static/image142.png?raw=true)

##### 2.1.2.9.3.4.2 **basicDetails** Hierarchy

Parent field: **studentsPrimaryDetails**

Child field(s):

<table class="field-properties-table"><thead><tr><td>Field</td><td>Type</td><td>Req</td><td>Key</td><td>Description</td><td>Comments</td></tr></thead><tbody><tr><td><a href=#9ed350d0-984f-11ec-a11a-61c866bfca96 class="margin-NaN">email</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#cecde0c0-984f-11ec-a11a-61c866bfca96 class="margin-NaN">firstName</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#d073efa0-984f-11ec-a11a-61c866bfca96 class="margin-NaN">middleName</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#d25cfaf0-984f-11ec-a11a-61c866bfca96 class="margin-NaN">lastName</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#e6cce9f0-984f-11ec-a11a-61c866bfca96 class="margin-NaN">nationality</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#f5053400-984f-11ec-a11a-61c866bfca96 class="margin-NaN">mob</a></td><td class="no-break-word">numeric</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#fb44a120-984f-11ec-a11a-61c866bfca96 class="margin-NaN">DOB</a></td><td class="no-break-word">date</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#032a9250-9850-11ec-a11a-61c866bfca96 class="margin-NaN">gender</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"><p>MALE/FEMALE/TRANS</p></div></td></tr><tr><td><a href=#0aeccee0-9850-11ec-a11a-61c866bfca96 class="margin-NaN">category</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#157be710-9850-11ec-a11a-61c866bfca96 class="margin-NaN">para-ability</a></td><td class="no-break-word">document</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"><p>is student suffers from any disability</p></div></td></tr></tbody></table>

##### 2.1.2.9.3.4.3 **basicDetails** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>basicDetails</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>document</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>DBRef</td><td></td></tr><tr><td>Min Properties</td><td></td></tr><tr><td>Max Properties</td><td></td></tr><tr><td>Additional properties</td><td>false</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="9ed350d0-984f-11ec-a11a-61c866bfca96"></a>2.1.2.9.3.5 Field **email**

##### 2.1.2.9.3.5.1 **email** Tree Diagram

![Hackolade image](static/image143.png?raw=true)

##### 2.1.2.9.3.5.2 **email** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>email</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="cecde0c0-984f-11ec-a11a-61c866bfca96"></a>2.1.2.9.3.6 Field **firstName**

##### 2.1.2.9.3.6.1 **firstName** Tree Diagram

![Hackolade image](static/image144.png?raw=true)

##### 2.1.2.9.3.6.2 **firstName** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>firstName</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="d073efa0-984f-11ec-a11a-61c866bfca96"></a>2.1.2.9.3.7 Field **middleName**

##### 2.1.2.9.3.7.1 **middleName** Tree Diagram

![Hackolade image](static/image145.png?raw=true)

##### 2.1.2.9.3.7.2 **middleName** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>middleName</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="d25cfaf0-984f-11ec-a11a-61c866bfca96"></a>2.1.2.9.3.8 Field **lastName**

##### 2.1.2.9.3.8.1 **lastName** Tree Diagram

![Hackolade image](static/image146.png?raw=true)

##### 2.1.2.9.3.8.2 **lastName** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>lastName</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="e6cce9f0-984f-11ec-a11a-61c866bfca96"></a>2.1.2.9.3.9 Field **nationality**

##### 2.1.2.9.3.9.1 **nationality** Tree Diagram

![Hackolade image](static/image147.png?raw=true)

##### 2.1.2.9.3.9.2 **nationality** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>nationality</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="f5053400-984f-11ec-a11a-61c866bfca96"></a>2.1.2.9.3.10 Field **mob**

##### 2.1.2.9.3.10.1 **mob** Tree Diagram

![Hackolade image](static/image148.png?raw=true)

##### 2.1.2.9.3.10.2 **mob** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>mob</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>numeric</td></tr><tr><td>Subtype</td><td></td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Unit</td><td></td></tr><tr><td>Min value</td><td></td></tr><tr><td>Excl min</td><td></td></tr><tr><td>Max value</td><td></td></tr><tr><td>Excl max</td><td></td></tr><tr><td>Multiple of</td><td></td></tr><tr><td>Divisible by</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="fb44a120-984f-11ec-a11a-61c866bfca96"></a>2.1.2.9.3.11 Field **DOB**

##### 2.1.2.9.3.11.1 **DOB** Tree Diagram

![Hackolade image](static/image149.png?raw=true)

##### 2.1.2.9.3.11.2 **DOB** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>DOB</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>date</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td>false</td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Now</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="032a9250-9850-11ec-a11a-61c866bfca96"></a>2.1.2.9.3.12 Field **gender**

##### 2.1.2.9.3.12.1 **gender** Tree Diagram

![Hackolade image](static/image150.png?raw=true)

##### 2.1.2.9.3.12.2 **gender** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>gender</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"><p>MALE/FEMALE/TRANS</p></div></td></tr></tbody></table>

### <a id="0aeccee0-9850-11ec-a11a-61c866bfca96"></a>2.1.2.9.3.13 Field **category**

##### 2.1.2.9.3.13.1 **category** Tree Diagram

![Hackolade image](static/image151.png?raw=true)

##### 2.1.2.9.3.13.2 **category** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>category</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="157be710-9850-11ec-a11a-61c866bfca96"></a>2.1.2.9.3.14 Field **para-ability**

##### 2.1.2.9.3.14.1 **para-ability** Tree Diagram

![Hackolade image](static/image152.png?raw=true)

##### 2.1.2.9.3.14.2 **para-ability** Hierarchy

Parent field: **basicDetails**

Child field(s):

<table class="field-properties-table"><thead><tr><td>Field</td><td>Type</td><td>Req</td><td>Key</td><td>Description</td><td>Comments</td></tr></thead><tbody><tr><td><a href=#34a6b930-9850-11ec-a11a-61c866bfca96 class="margin-NaN">isDisable</a></td><td class="no-break-word">boolean</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#4422cde0-9850-11ec-a11a-61c866bfca96 class="margin-NaN">nameOfDisability</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr></tbody></table>

##### 2.1.2.9.3.14.3 **para-ability** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>para-ability</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>document</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>DBRef</td><td></td></tr><tr><td>Min Properties</td><td></td></tr><tr><td>Max Properties</td><td></td></tr><tr><td>Additional properties</td><td>false</td></tr><tr><td>Comments</td><td><div class="docs-markdown"><p>is student suffers from any disability</p></div></td></tr></tbody></table>

### <a id="34a6b930-9850-11ec-a11a-61c866bfca96"></a>2.1.2.9.3.15 Field **isDisable**

##### 2.1.2.9.3.15.1 **isDisable** Tree Diagram

![Hackolade image](static/image153.png?raw=true)

##### 2.1.2.9.3.15.2 **isDisable** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>isDisable</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>boolean</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="4422cde0-9850-11ec-a11a-61c866bfca96"></a>2.1.2.9.3.16 Field **nameOfDisability**

##### 2.1.2.9.3.16.1 **nameOfDisability** Tree Diagram

![Hackolade image](static/image154.png?raw=true)

##### 2.1.2.9.3.16.2 **nameOfDisability** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>nameOfDisability</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="6d5970b0-984b-11ec-a11a-61c866bfca96"></a>2.1.2.9.3.17 Field **addressDetails**

##### 2.1.2.9.3.17.1 **addressDetails** Tree Diagram

![Hackolade image](static/image155.png?raw=true)

##### 2.1.2.9.3.17.2 **addressDetails** Hierarchy

Parent field: **studentsPrimaryDetails**

Child field(s):

<table class="field-properties-table"><thead><tr><td>Field</td><td>Type</td><td>Req</td><td>Key</td><td>Description</td><td>Comments</td></tr></thead><tbody><tr><td><a href=#727d34a0-984b-11ec-a11a-61c866bfca96 class="margin-NaN">city</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#7832b140-984b-11ec-a11a-61c866bfca96 class="margin-NaN">state</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#7b144d60-984b-11ec-a11a-61c866bfca96 class="margin-NaN">country</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr></tbody></table>

##### 2.1.2.9.3.17.3 **addressDetails** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>addressDetails</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>document</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>DBRef</td><td></td></tr><tr><td>Min Properties</td><td></td></tr><tr><td>Max Properties</td><td></td></tr><tr><td>Additional properties</td><td>false</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="727d34a0-984b-11ec-a11a-61c866bfca96"></a>2.1.2.9.3.18 Field **city**

##### 2.1.2.9.3.18.1 **city** Tree Diagram

![Hackolade image](static/image156.png?raw=true)

##### 2.1.2.9.3.18.2 **city** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>city</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="7832b140-984b-11ec-a11a-61c866bfca96"></a>2.1.2.9.3.19 Field **state**

##### 2.1.2.9.3.19.1 **state** Tree Diagram

![Hackolade image](static/image157.png?raw=true)

##### 2.1.2.9.3.19.2 **state** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>state</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="7b144d60-984b-11ec-a11a-61c866bfca96"></a>2.1.2.9.3.20 Field **country**

##### 2.1.2.9.3.20.1 **country** Tree Diagram

![Hackolade image](static/image158.png?raw=true)

##### 2.1.2.9.3.20.2 **country** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>country</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="18d38870-984e-11ec-a11a-61c866bfca96"></a>2.1.2.9.3.21 Field **courseDetails**

##### 2.1.2.9.3.21.1 **courseDetails** Tree Diagram

![Hackolade image](static/image159.png?raw=true)

##### 2.1.2.9.3.21.2 **courseDetails** Hierarchy

Parent field: **studentsPrimaryDetails**

Child field(s):

<table class="field-properties-table"><thead><tr><td>Field</td><td>Type</td><td>Req</td><td>Key</td><td>Description</td><td>Comments</td></tr></thead><tbody><tr><td><a href=#18d8b890-984e-11ec-a11a-61c866bfca96 class="margin-NaN">[0]&nbsp;courseInfo</a></td><td class="no-break-word">document</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr></tbody></table>

##### 2.1.2.9.3.21.3 **courseDetails** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>courseDetails</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>array</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Min items</td><td>0</td></tr><tr><td>Max items</td><td>3</td></tr><tr><td>Unique items</td><td></td></tr><tr><td>Additional items</td><td>true</td></tr><tr><td>Comments</td><td><div class="docs-markdown"><p>array size cannot be more than 3</p></div></td></tr></tbody></table>

### <a id="18d8b890-984e-11ec-a11a-61c866bfca96"></a>2.1.2.9.3.22 Field **\[0\] courseInfo**

##### 2.1.2.9.3.22.1 **\[0\] courseInfo** Tree Diagram

![Hackolade image](static/image160.png?raw=true)

##### 2.1.2.9.3.22.2 **\[0\] courseInfo** Hierarchy

Parent field: **courseDetails**

Child field(s):

<table class="field-properties-table"><thead><tr><td>Field</td><td>Type</td><td>Req</td><td>Key</td><td>Description</td><td>Comments</td></tr></thead><tbody><tr><td><a href=#3afc3140-984e-11ec-a11a-61c866bfca96 class="margin-NaN">courseId</a></td><td class="no-break-word">objectId</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#3b0950a0-984e-11ec-a11a-61c866bfca96 class="margin-NaN">courseName</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#fc955980-984e-11ec-a11a-61c866bfca96 class="margin-NaN">applicationID</a></td><td class="no-break-word">objectId</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#08231d00-984f-11ec-a11a-61c866bfca96 class="margin-NaN">status</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"><p>student is enrolled or payment is due</p></div></td></tr><tr><td><a href=#bd1eb4e0-984e-11ec-a11a-61c866bfca96 class="margin-NaN">specs</a></td><td class="no-break-word">array</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr></tbody></table>

##### 2.1.2.9.3.22.3 **\[0\] courseInfo** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Display name</td><td>courseInfo</td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>document</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>DBRef</td><td></td></tr><tr><td>Min Properties</td><td></td></tr><tr><td>Max Properties</td><td></td></tr><tr><td>Additional properties</td><td>false</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="3afc3140-984e-11ec-a11a-61c866bfca96"></a>2.1.2.9.3.23 Field **courseId**

##### 2.1.2.9.3.23.1 **courseId** Tree Diagram

![Hackolade image](static/image161.png?raw=true)

##### 2.1.2.9.3.23.2 **courseId** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>courseId</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>objectId</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td><a href=#6fe13ff0-983e-11ec-a11a-61c866bfca96>Courses</a></td></tr><tr><td>Foreign field</td><td><a href=#6d894200-9845-11ec-a11a-61c866bfca96>courseId</a></td></tr><tr><td>Relationship type</td><td>Foreign Key</td></tr><tr><td>Relationship name</td><td>fk Courses. to Students.</td></tr><tr><td>Cardinality</td><td>n</td></tr><tr><td>Default</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="3b0950a0-984e-11ec-a11a-61c866bfca96"></a>2.1.2.9.3.24 Field **courseName**

##### 2.1.2.9.3.24.1 **courseName** Tree Diagram

![Hackolade image](static/image162.png?raw=true)

##### 2.1.2.9.3.24.2 **courseName** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>courseName</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td><a href=#6fe13ff0-983e-11ec-a11a-61c866bfca96>Courses</a></td></tr><tr><td>Foreign field</td><td><a href=#7683d780-9845-11ec-a11a-61c866bfca96>courseName</a></td></tr><tr><td>Relationship type</td><td>Foreign Key</td></tr><tr><td>Relationship name</td><td>fk Courses. to Students.</td></tr><tr><td>Cardinality</td><td>n</td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="fc955980-984e-11ec-a11a-61c866bfca96"></a>2.1.2.9.3.25 Field **applicationID**

##### 2.1.2.9.3.25.1 **applicationID** Tree Diagram

![Hackolade image](static/image163.png?raw=true)

##### 2.1.2.9.3.25.2 **applicationID** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>applicationID</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>objectId</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td><a href=#86e576f0-9855-11ec-a11a-61c866bfca96>studentApplicationForms</a></td></tr><tr><td>Foreign field</td><td><a href=#2605b2e0-98ab-11ec-a8e6-f363f79d3ea0>applicationId</a></td></tr><tr><td>Relationship type</td><td>Foreign Key</td></tr><tr><td>Relationship name</td><td>fk studentApplicationForms. to studentsPrimaryDetails.</td></tr><tr><td>Cardinality</td><td>1</td></tr><tr><td>Default</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="08231d00-984f-11ec-a11a-61c866bfca96"></a>2.1.2.9.3.26 Field **status**

##### 2.1.2.9.3.26.1 **status** Tree Diagram

![Hackolade image](static/image164.png?raw=true)

##### 2.1.2.9.3.26.2 **status** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>status</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Sample</td><td>Enrolled</td></tr><tr><td>Comments</td><td><div class="docs-markdown"><p>student is enrolled or payment is due</p></div></td></tr></tbody></table>

### <a id="bd1eb4e0-984e-11ec-a11a-61c866bfca96"></a>2.1.2.9.3.27 Field **specs**

##### 2.1.2.9.3.27.1 **specs** Tree Diagram

![Hackolade image](static/image165.png?raw=true)

##### 2.1.2.9.3.27.2 **specs** Hierarchy

Parent field: **\[0\] courseInfo**

Child field(s):

<table class="field-properties-table"><thead><tr><td>Field</td><td>Type</td><td>Req</td><td>Key</td><td>Description</td><td>Comments</td></tr></thead><tbody><tr><td><a href=#bd243320-984e-11ec-a11a-61c866bfca96 class="margin-NaN">[0]</a></td><td class="no-break-word">document</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr></tbody></table>

##### 2.1.2.9.3.27.3 **specs** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>specs</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>array</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>Min items</td><td></td></tr><tr><td>Max items</td><td></td></tr><tr><td>Unique items</td><td></td></tr><tr><td>Additional items</td><td>true</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="bd243320-984e-11ec-a11a-61c866bfca96"></a>2.1.2.9.3.28 Field **\[0\]**

##### 2.1.2.9.3.28.1 **\[0\]** Tree Diagram

![Hackolade image](static/image166.png?raw=true)

##### 2.1.2.9.3.28.2 **\[0\]** Hierarchy

Parent field: **specs**

Child field(s):

<table class="field-properties-table"><thead><tr><td>Field</td><td>Type</td><td>Req</td><td>Key</td><td>Description</td><td>Comments</td></tr></thead><tbody><tr><td><a href=#c9ce3c10-984e-11ec-a11a-61c866bfca96 class="margin-NaN">specId</a></td><td class="no-break-word">objectId</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr><tr><td><a href=#c9da7110-984e-11ec-a11a-61c866bfca96 class="margin-NaN">specName</a></td><td class="no-break-word">string</td><td>false</td><td></td><td><div class="docs-markdown"></div></td><td><div class="docs-markdown"></div></td></tr></tbody></table>

##### 2.1.2.9.3.28.3 **\[0\]** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Display name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>document</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td></td></tr><tr><td>Foreign field</td><td></td></tr><tr><td>Relationship type</td><td></td></tr><tr><td>Relationship name</td><td></td></tr><tr><td>Cardinality</td><td></td></tr><tr><td>DBRef</td><td></td></tr><tr><td>Min Properties</td><td></td></tr><tr><td>Max Properties</td><td></td></tr><tr><td>Additional properties</td><td>false</td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="c9ce3c10-984e-11ec-a11a-61c866bfca96"></a>2.1.2.9.3.29 Field **specId**

##### 2.1.2.9.3.29.1 **specId** Tree Diagram

![Hackolade image](static/image167.png?raw=true)

##### 2.1.2.9.3.29.2 **specId** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>specId</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>objectId</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Foreign collection</td><td><a href=#01333ab0-9846-11ec-a11a-61c866bfca96>specializations</a></td></tr><tr><td>Foreign field</td><td><a href=#142f0040-9846-11ec-a11a-61c866bfca96>id</a></td></tr><tr><td>Relationship type</td><td>Foreign Key</td></tr><tr><td>Relationship name</td><td>New Relationship</td></tr><tr><td>Cardinality</td><td>n</td></tr><tr><td>Default</td><td></td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

### <a id="c9da7110-984e-11ec-a11a-61c866bfca96"></a>2.1.2.9.3.30 Field **specName**

##### 2.1.2.9.3.30.1 **specName** Tree Diagram

![Hackolade image](static/image168.png?raw=true)

##### 2.1.2.9.3.30.2 **specName** properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>specName</td></tr><tr><td>Technical name</td><td></td></tr><tr><td>Activated</td><td>true</td></tr><tr><td>Id</td><td></td></tr><tr><td>Type</td><td>string</td></tr><tr><td>Description</td><td><div class="docs-markdown"></div></td></tr><tr><td>Format</td><td></td></tr><tr><td>Pattern</td><td></td></tr><tr><td>Min length</td><td></td></tr><tr><td>Max length</td><td></td></tr><tr><td>Default</td><td></td></tr><tr><td>Enum</td><td></td></tr><tr><td>Required</td><td></td></tr><tr><td>Primary key</td><td></td></tr><tr><td>Dependencies</td><td></td></tr><tr><td>Foreign collection</td><td><a href=#01333ab0-9846-11ec-a11a-61c866bfca96>specializations</a></td></tr><tr><td>Foreign field</td><td><a href=#29e1cf80-9846-11ec-a11a-61c866bfca96>name</a></td></tr><tr><td>Relationship type</td><td>Foreign Key</td></tr><tr><td>Relationship name</td><td>New Relationship(1)</td></tr><tr><td>Cardinality</td><td>n</td></tr><tr><td>Sample</td><td></td></tr><tr><td>Comments</td><td><div class="docs-markdown"></div></td></tr></tbody></table>

##### 2.1.2.9.4 **studentsPrimaryDetails** JSON Schema

```
{
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "title": "studentsPrimaryDetails",
    "properties": {
        "id": {
            "type": "string",
            "pattern": "^[a-fA-F0-9]{24}$"
        },
        "userName": {
            "type": "string"
        },
        "pwd": {
            "type": "string"
        },
        "basicDetails": {
            "type": "object",
            "properties": {
                "email": {
                    "type": "string"
                },
                "firstName": {
                    "type": "string"
                },
                "middleName": {
                    "type": "string"
                },
                "lastName": {
                    "type": "string"
                },
                "nationality": {
                    "type": "string"
                },
                "mob": {
                    "type": "number"
                },
                "DOB": {
                    "type": "string",
                    "format": "date-time"
                },
                "gender": {
                    "type": "string"
                },
                "category": {
                    "type": "string"
                },
                "para-ability": {
                    "type": "object",
                    "properties": {
                        "isDisable": {
                            "type": "boolean"
                        },
                        "nameOfDisability": {
                            "type": "string"
                        }
                    },
                    "additionalProperties": false
                }
            },
            "additionalProperties": false
        },
        "addressDetails": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string"
                },
                "state": {
                    "type": "string"
                },
                "country": {
                    "type": "string"
                }
            },
            "additionalProperties": false
        },
        "courseDetails": {
            "type": "array",
            "additionalItems": true,
            "maxItems": 3,
            "minItems": 0,
            "items": {
                "type": "object",
                "properties": {
                    "courseId": {
                        "type": "string",
                        "pattern": "^[a-fA-F0-9]{24}$"
                    },
                    "courseName": {
                        "type": "string"
                    },
                    "applicationID": {
                        "type": "string",
                        "pattern": "^[a-fA-F0-9]{24}$"
                    },
                    "status": {
                        "type": "string"
                    },
                    "specs": {
                        "type": "array",
                        "additionalItems": true,
                        "items": {
                            "type": "object",
                            "properties": {
                                "specId": {
                                    "type": "string",
                                    "pattern": "^[a-fA-F0-9]{24}$"
                                },
                                "specName": {
                                    "type": "string"
                                }
                            },
                            "additionalProperties": false
                        }
                    }
                },
                "additionalProperties": false
            }
        }
    },
    "additionalProperties": false
}
```

##### 2.1.2.9.5 **studentsPrimaryDetails** JSON data

```
{
    "id": ObjectId("507f1f77bcf86cd799439011"),
    "userName": "Lorem",
    "pwd": "Lorem",
    "basicDetails": {
        "email": "Lorem",
        "firstName": "Lorem",
        "middleName": "Lorem",
        "lastName": "Lorem",
        "nationality": "Lorem",
        "mob": -64,
        "DOB": ISODate("2016-04-08T15:06:21.595Z"),
        "gender": "Lorem",
        "category": "Lorem",
        "para-ability": {
            "isDisable": true,
            "nameOfDisability": "Lorem"
        }
    },
    "addressDetails": {
        "city": "Lorem",
        "state": "Lorem",
        "country": "Lorem"
    },
    "courseDetails": [
        {
            "courseId": ObjectId("507f1f77bcf86cd799439011"),
            "courseName": "Lorem",
            "applicationID": ObjectId("507f1f77bcf86cd799439011"),
            "status": "Enrolled",
            "specs": [
                {
                    "specId": ObjectId("507f1f77bcf86cd799439011"),
                    "specName": "Lorem"
                }
            ]
        }
    ]
}
```

##### 2.1.2.9.6 **studentsPrimaryDetails** Target Script

```
db.createCollection("studentsPrimaryDetails", {
    "storageEngine": {
        "wiredTiger": {}
    },
    "capped": false,
    "validator": {
        "$jsonSchema": {
            "bsonType": "object",
            "title": "studentsPrimaryDetails",
            "properties": {
                "_id": {
                    "bsonType": "objectId"
                },
                "id": {
                    "bsonType": "objectId"
                },
                "userName": {
                    "bsonType": "string"
                },
                "pwd": {
                    "bsonType": "string"
                },
                "basicDetails": {
                    "bsonType": "object",
                    "properties": {
                        "email": {
                            "bsonType": "string"
                        },
                        "firstName": {
                            "bsonType": "string"
                        },
                        "middleName": {
                            "bsonType": "string"
                        },
                        "lastName": {
                            "bsonType": "string"
                        },
                        "nationality": {
                            "bsonType": "string"
                        },
                        "mob": {
                            "bsonType": "number"
                        },
                        "DOB": {
                            "bsonType": "date"
                        },
                        "gender": {
                            "bsonType": "string"
                        },
                        "category": {
                            "bsonType": "string"
                        },
                        "para-ability": {
                            "bsonType": "object",
                            "properties": {
                                "isDisable": {
                                    "bsonType": "bool"
                                },
                                "nameOfDisability": {
                                    "bsonType": "string"
                                }
                            },
                            "additionalProperties": false
                        }
                    },
                    "additionalProperties": false
                },
                "addressDetails": {
                    "bsonType": "object",
                    "properties": {
                        "city": {
                            "bsonType": "string"
                        },
                        "state": {
                            "bsonType": "string"
                        },
                        "country": {
                            "bsonType": "string"
                        }
                    },
                    "additionalProperties": false
                },
                "courseDetails": {
                    "bsonType": "array",
                    "additionalItems": true,
                    "maxItems": 3,
                    "minItems": 0,
                    "items": {
                        "bsonType": "object",
                        "properties": {
                            "courseId": {
                                "bsonType": "objectId"
                            },
                            "courseName": {
                                "bsonType": "string"
                            },
                            "applicationID": {
                                "bsonType": "objectId"
                            },
                            "status": {
                                "bsonType": "string"
                            },
                            "specs": {
                                "bsonType": "array",
                                "additionalItems": true,
                                "items": {
                                    "bsonType": "object",
                                    "properties": {
                                        "specId": {
                                            "bsonType": "objectId"
                                        },
                                        "specName": {
                                            "bsonType": "string"
                                        }
                                    },
                                    "additionalProperties": false
                                }
                            }
                        },
                        "additionalProperties": false
                    }
                }
            },
            "additionalProperties": false
        }
    },
    "validationLevel": "off",
    "validationAction": "warn"
});
```

### <a id="relationships"></a>

##### 3\. Relationships

### <a id="c9ce6320-984e-11ec-a11a-61c866bfca96"></a>3.1 Relationship **New Relationship**

##### 3.1.1 **New Relationship** Diagram

<table><thead><tr><td>Parent Table</td><td>Parent field</td></tr></thead><tbody><tr><td><a href=#01333ab0-9846-11ec-a11a-61c866bfca96>specializations</a></td><td><a href=#142f0040-9846-11ec-a11a-61c866bfca96>id</a></td></tr></tbody></table>

![Hackolade image](static/image169.png?raw=true)![Hackolade image](static/image170.png?raw=true)

<table><thead><tr><td>Child Table</td><td>Child field</td></tr></thead><tbody><tr><td><a href=#64c55110-983e-11ec-a11a-61c866bfca96>studentsPrimaryDetails</a></td><td><a href=#c9ce3c10-984e-11ec-a11a-61c866bfca96>courseDetails.[-1].specs.[-1].specId</a></td></tr></tbody></table>

##### 3.1.2 **New Relationship** Properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>New Relationship</td></tr><tr><td>Description</td><td></td></tr><tr><td>Parent Collection</td><td><a href=#01333ab0-9846-11ec-a11a-61c866bfca96>specializations</a></td></tr><tr><td>Parent field</td><td><a href=#142f0040-9846-11ec-a11a-61c866bfca96>id</a></td></tr><tr><td>Parent Cardinality</td><td>n</td></tr><tr><td>Child Collection</td><td><a href=#64c55110-983e-11ec-a11a-61c866bfca96>studentsPrimaryDetails</a></td></tr><tr><td>Child field</td><td><a href=#c9ce3c10-984e-11ec-a11a-61c866bfca96>specId</a></td></tr><tr><td>Child Cardinality</td><td>n</td></tr><tr><td>Comments</td><td></td></tr></tbody></table>

### <a id="c9da9820-984e-11ec-a11a-61c866bfca96"></a>3.2 Relationship **New Relationship(1)**

##### 3.2.1 **New Relationship(1)** Diagram

<table><thead><tr><td>Parent Table</td><td>Parent field</td></tr></thead><tbody><tr><td><a href=#01333ab0-9846-11ec-a11a-61c866bfca96>specializations</a></td><td><a href=#29e1cf80-9846-11ec-a11a-61c866bfca96>name</a></td></tr></tbody></table>

![Hackolade image](static/image171.png?raw=true)![Hackolade image](static/image172.png?raw=true)

<table><thead><tr><td>Child Table</td><td>Child field</td></tr></thead><tbody><tr><td><a href=#64c55110-983e-11ec-a11a-61c866bfca96>studentsPrimaryDetails</a></td><td><a href=#c9da7110-984e-11ec-a11a-61c866bfca96>courseDetails.[-1].specs.[-1].specName</a></td></tr></tbody></table>

##### 3.2.2 **New Relationship(1)** Properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>New Relationship(1)</td></tr><tr><td>Description</td><td></td></tr><tr><td>Parent Collection</td><td><a href=#01333ab0-9846-11ec-a11a-61c866bfca96>specializations</a></td></tr><tr><td>Parent field</td><td><a href=#29e1cf80-9846-11ec-a11a-61c866bfca96>name</a></td></tr><tr><td>Parent Cardinality</td><td>n</td></tr><tr><td>Child Collection</td><td><a href=#64c55110-983e-11ec-a11a-61c866bfca96>studentsPrimaryDetails</a></td></tr><tr><td>Child field</td><td><a href=#c9da7110-984e-11ec-a11a-61c866bfca96>specName</a></td></tr><tr><td>Child Cardinality</td><td>n</td></tr><tr><td>Comments</td><td></td></tr></tbody></table>

### <a id="94c3fb80-9845-11ec-a11a-61c866bfca96"></a>3.3 Relationship **fk Client. to Courses.**

##### 3.3.1 **fk Client. to Courses.** Diagram

<table><thead><tr><td>Parent Table</td><td>Parent field</td></tr></thead><tbody><tr><td><a href=#28ec4d90-97e6-11ec-9947-b7f0ab1a4e72>Client</a></td><td><a href=#39b8b000-97e6-11ec-9947-b7f0ab1a4e72>client_id</a></td></tr></tbody></table>

![Hackolade image](static/image173.png?raw=true)![Hackolade image](static/image174.png?raw=true)

<table><thead><tr><td>Child Table</td><td>Child field</td></tr></thead><tbody><tr><td><a href=#6fe13ff0-983e-11ec-a11a-61c866bfca96>Courses</a></td><td><a href=#89d3d790-9845-11ec-a11a-61c866bfca96>clientId</a></td></tr></tbody></table>

##### 3.3.2 **fk Client. to Courses.** Properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>fk Client. to Courses.</td></tr><tr><td>Description</td><td></td></tr><tr><td>Parent Collection</td><td><a href=#28ec4d90-97e6-11ec-9947-b7f0ab1a4e72>Client</a></td></tr><tr><td>Parent field</td><td><a href=#39b8b000-97e6-11ec-9947-b7f0ab1a4e72>client_id</a></td></tr><tr><td>Parent Cardinality</td><td>1</td></tr><tr><td>Child Collection</td><td><a href=#6fe13ff0-983e-11ec-a11a-61c866bfca96>Courses</a></td></tr><tr><td>Child field</td><td><a href=#89d3d790-9845-11ec-a11a-61c866bfca96>clientId</a></td></tr><tr><td>Child Cardinality</td><td>n</td></tr><tr><td>Comments</td><td></td></tr></tbody></table>

### <a id="43b90370-97eb-11ec-a19e-9d6e67c760cd"></a>3.4 Relationship **fk Client. to Users.**

##### 3.4.1 **fk Client. to Users.** Diagram

<table><thead><tr><td>Parent Table</td><td>Parent field</td></tr></thead><tbody><tr><td><a href=#28ec4d90-97e6-11ec-9947-b7f0ab1a4e72>Client</a></td><td><a href=#39b8b000-97e6-11ec-9947-b7f0ab1a4e72>client_id</a></td></tr></tbody></table>

![Hackolade image](static/image175.png?raw=true)![Hackolade image](static/image176.png?raw=true)

<table><thead><tr><td>Child Table</td><td>Child field</td></tr></thead><tbody><tr><td><a href=#7be6d480-97db-11ec-9947-b7f0ab1a4e72>Users</a></td><td><a href=#a77ba3e0-97dc-11ec-9947-b7f0ab1a4e72>client_id</a></td></tr></tbody></table>

##### 3.4.2 **fk Client. to Users.** Properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>fk Client. to Users.</td></tr><tr><td>Description</td><td></td></tr><tr><td>Parent Collection</td><td><a href=#28ec4d90-97e6-11ec-9947-b7f0ab1a4e72>Client</a></td></tr><tr><td>Parent field</td><td><a href=#39b8b000-97e6-11ec-9947-b7f0ab1a4e72>client_id</a></td></tr><tr><td>Parent Cardinality</td><td>1</td></tr><tr><td>Child Collection</td><td><a href=#7be6d480-97db-11ec-9947-b7f0ab1a4e72>Users</a></td></tr><tr><td>Child field</td><td><a href=#a77ba3e0-97dc-11ec-9947-b7f0ab1a4e72>client_id</a></td></tr><tr><td>Child Cardinality</td><td>n</td></tr><tr><td>Comments</td><td></td></tr></tbody></table>

### <a id="3afc3142-984e-11ec-a11a-61c866bfca96"></a>3.5 Relationship **fk Courses. to Students.**

##### 3.5.1 **fk Courses. to Students.** Diagram

<table><thead><tr><td>Parent Table</td><td>Parent field</td></tr></thead><tbody><tr><td><a href=#6fe13ff0-983e-11ec-a11a-61c866bfca96>Courses</a></td><td><a href=#6d894200-9845-11ec-a11a-61c866bfca96>courseId</a></td></tr></tbody></table>

![Hackolade image](static/image177.png?raw=true)![Hackolade image](static/image178.png?raw=true)

<table><thead><tr><td>Child Table</td><td>Child field</td></tr></thead><tbody><tr><td><a href=#64c55110-983e-11ec-a11a-61c866bfca96>studentsPrimaryDetails</a></td><td><a href=#3afc3140-984e-11ec-a11a-61c866bfca96>courseDetails.[-1].courseId</a></td></tr></tbody></table>

##### 3.5.2 **fk Courses. to Students.** Properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>fk Courses. to Students.</td></tr><tr><td>Description</td><td></td></tr><tr><td>Parent Collection</td><td><a href=#6fe13ff0-983e-11ec-a11a-61c866bfca96>Courses</a></td></tr><tr><td>Parent field</td><td><a href=#6d894200-9845-11ec-a11a-61c866bfca96>courseId</a></td></tr><tr><td>Parent Cardinality</td><td>n</td></tr><tr><td>Child Collection</td><td><a href=#64c55110-983e-11ec-a11a-61c866bfca96>studentsPrimaryDetails</a></td></tr><tr><td>Child field</td><td><a href=#3afc3140-984e-11ec-a11a-61c866bfca96>courseId</a></td></tr><tr><td>Child Cardinality</td><td>n</td></tr><tr><td>Comments</td><td></td></tr></tbody></table>

### <a id="3b0950a2-984e-11ec-a11a-61c866bfca96"></a>3.6 Relationship **fk Courses. to Students.**

##### 3.6.1 **fk Courses. to Students.** Diagram

<table><thead><tr><td>Parent Table</td><td>Parent field</td></tr></thead><tbody><tr><td><a href=#6fe13ff0-983e-11ec-a11a-61c866bfca96>Courses</a></td><td><a href=#7683d780-9845-11ec-a11a-61c866bfca96>courseName</a></td></tr></tbody></table>

![Hackolade image](static/image179.png?raw=true)![Hackolade image](static/image180.png?raw=true)

<table><thead><tr><td>Child Table</td><td>Child field</td></tr></thead><tbody><tr><td><a href=#64c55110-983e-11ec-a11a-61c866bfca96>studentsPrimaryDetails</a></td><td><a href=#3b0950a0-984e-11ec-a11a-61c866bfca96>courseDetails.[-1].[-1]</a></td></tr></tbody></table>

##### 3.6.2 **fk Courses. to Students.** Properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>fk Courses. to Students.</td></tr><tr><td>Description</td><td></td></tr><tr><td>Parent Collection</td><td><a href=#6fe13ff0-983e-11ec-a11a-61c866bfca96>Courses</a></td></tr><tr><td>Parent field</td><td><a href=#7683d780-9845-11ec-a11a-61c866bfca96>courseName</a></td></tr><tr><td>Parent Cardinality</td><td>n</td></tr><tr><td>Child Collection</td><td><a href=#64c55110-983e-11ec-a11a-61c866bfca96>studentsPrimaryDetails</a></td></tr><tr><td>Child field</td><td><a href=#3b0950a0-984e-11ec-a11a-61c866bfca96></a></td></tr><tr><td>Child Cardinality</td><td>n</td></tr><tr><td>Comments</td><td></td></tr></tbody></table>

### <a id="20a35330-9846-11ec-a11a-61c866bfca96"></a>3.7 Relationship **fk Courses. to specializations.**

##### 3.7.1 **fk Courses. to specializations.** Diagram

<table><thead><tr><td>Parent Table</td><td>Parent field</td></tr></thead><tbody><tr><td><a href=#6fe13ff0-983e-11ec-a11a-61c866bfca96>Courses</a></td><td><a href=#6d894200-9845-11ec-a11a-61c866bfca96>courseId</a></td></tr></tbody></table>

![Hackolade image](static/image181.png?raw=true)![Hackolade image](static/image182.png?raw=true)

<table><thead><tr><td>Child Table</td><td>Child field</td></tr></thead><tbody><tr><td><a href=#01333ab0-9846-11ec-a11a-61c866bfca96>specializations</a></td><td><a href=#19518bb0-9846-11ec-a11a-61c866bfca96>courseId</a></td></tr></tbody></table>

##### 3.7.2 **fk Courses. to specializations.** Properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>fk Courses. to specializations.</td></tr><tr><td>Description</td><td></td></tr><tr><td>Parent Collection</td><td><a href=#6fe13ff0-983e-11ec-a11a-61c866bfca96>Courses</a></td></tr><tr><td>Parent field</td><td><a href=#6d894200-9845-11ec-a11a-61c866bfca96>courseId</a></td></tr><tr><td>Parent Cardinality</td><td>1</td></tr><tr><td>Child Collection</td><td><a href=#01333ab0-9846-11ec-a11a-61c866bfca96>specializations</a></td></tr><tr><td>Child field</td><td><a href=#19518bb0-9846-11ec-a11a-61c866bfca96>courseId</a></td></tr><tr><td>Child Cardinality</td><td>n</td></tr><tr><td>Comments</td><td></td></tr></tbody></table>

### <a id="35badc20-98af-11ec-a8e6-f363f79d3ea0"></a>3.8 Relationship **fk Courses. to studentApplicationForms.**

##### 3.8.1 **fk Courses. to studentApplicationForms.** Diagram

<table><thead><tr><td>Parent Table</td><td>Parent field</td></tr></thead><tbody><tr><td><a href=#6fe13ff0-983e-11ec-a11a-61c866bfca96>Courses</a></td><td><a href=#6d894200-9845-11ec-a11a-61c866bfca96>courseId</a></td></tr></tbody></table>

![Hackolade image](static/image183.png?raw=true)![Hackolade image](static/image184.png?raw=true)

<table><thead><tr><td>Child Table</td><td>Child field</td></tr></thead><tbody><tr><td><a href=#86e576f0-9855-11ec-a11a-61c866bfca96>studentApplicationForms</a></td><td><a href=#5ee3a6d0-98ab-11ec-a8e6-f363f79d3ea0>courseId</a></td></tr></tbody></table>

##### 3.8.2 **fk Courses. to studentApplicationForms.** Properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>fk Courses. to studentApplicationForms.</td></tr><tr><td>Description</td><td></td></tr><tr><td>Parent Collection</td><td><a href=#6fe13ff0-983e-11ec-a11a-61c866bfca96>Courses</a></td></tr><tr><td>Parent field</td><td><a href=#6d894200-9845-11ec-a11a-61c866bfca96>courseId</a></td></tr><tr><td>Parent Cardinality</td><td>1</td></tr><tr><td>Child Collection</td><td><a href=#86e576f0-9855-11ec-a11a-61c866bfca96>studentApplicationForms</a></td></tr><tr><td>Child field</td><td><a href=#5ee3a6d0-98ab-11ec-a8e6-f363f79d3ea0>courseId</a></td></tr><tr><td>Child Cardinality</td><td>n</td></tr><tr><td>Comments</td><td></td></tr></tbody></table>

### <a id="022c4480-97f5-11ec-8040-bdb9a5c9bfef"></a>3.9 Relationship **fk Roles. to Users.**

##### 3.9.1 **fk Roles. to Users.** Diagram

<table><thead><tr><td>Parent Table</td><td>Parent field</td></tr></thead><tbody><tr><td><a href=#675aa9f0-97e6-11ec-9947-b7f0ab1a4e72>Roles</a></td><td><a href=#516c62e0-97e7-11ec-9947-b7f0ab1a4e72>id</a></td></tr></tbody></table>

![Hackolade image](static/image185.png?raw=true)![Hackolade image](static/image186.png?raw=true)

<table><thead><tr><td>Child Table</td><td>Child field</td></tr></thead><tbody><tr><td><a href=#7be6d480-97db-11ec-9947-b7f0ab1a4e72>Users</a></td><td><a href=#f8d11870-97f4-11ec-8040-bdb9a5c9bfef>role.id</a></td></tr></tbody></table>

##### 3.9.2 **fk Roles. to Users.** Properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>fk Roles. to Users.</td></tr><tr><td>Description</td><td></td></tr><tr><td>Parent Collection</td><td><a href=#675aa9f0-97e6-11ec-9947-b7f0ab1a4e72>Roles</a></td></tr><tr><td>Parent field</td><td><a href=#516c62e0-97e7-11ec-9947-b7f0ab1a4e72>id</a></td></tr><tr><td>Parent Cardinality</td><td>1</td></tr><tr><td>Child Collection</td><td><a href=#7be6d480-97db-11ec-9947-b7f0ab1a4e72>Users</a></td></tr><tr><td>Child field</td><td><a href=#f8d11870-97f4-11ec-8040-bdb9a5c9bfef>id</a></td></tr><tr><td>Child Cardinality</td><td>1</td></tr><tr><td>Comments</td><td></td></tr></tbody></table>

### <a id="1f3bd7c0-97f5-11ec-8040-bdb9a5c9bfef"></a>3.10 Relationship **fk Roles. to Users.**

##### 3.10.1 **fk Roles. to Users.** Diagram

<table><thead><tr><td>Parent Table</td><td>Parent field</td></tr></thead><tbody><tr><td><a href=#675aa9f0-97e6-11ec-9947-b7f0ab1a4e72>Roles</a></td><td><a href=#c9ce41e0-97e7-11ec-9947-b7f0ab1a4e72>roleName</a></td></tr></tbody></table>

![Hackolade image](static/image187.png?raw=true)![Hackolade image](static/image188.png?raw=true)

<table><thead><tr><td>Child Table</td><td>Child field</td></tr></thead><tbody><tr><td><a href=#7be6d480-97db-11ec-9947-b7f0ab1a4e72>Users</a></td><td><a href=#0be4abc0-97f5-11ec-8040-bdb9a5c9bfef>role.roleName</a></td></tr></tbody></table>

##### 3.10.2 **fk Roles. to Users.** Properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>fk Roles. to Users.</td></tr><tr><td>Description</td><td></td></tr><tr><td>Parent Collection</td><td><a href=#675aa9f0-97e6-11ec-9947-b7f0ab1a4e72>Roles</a></td></tr><tr><td>Parent field</td><td><a href=#c9ce41e0-97e7-11ec-9947-b7f0ab1a4e72>roleName</a></td></tr><tr><td>Parent Cardinality</td><td>1</td></tr><tr><td>Child Collection</td><td><a href=#7be6d480-97db-11ec-9947-b7f0ab1a4e72>Users</a></td></tr><tr><td>Child field</td><td><a href=#0be4abc0-97f5-11ec-8040-bdb9a5c9bfef>roleName</a></td></tr><tr><td>Child Cardinality</td><td>1</td></tr><tr><td>Comments</td><td></td></tr></tbody></table>

### <a id="7bbdfc70-98af-11ec-a8e6-f363f79d3ea0"></a>3.11 Relationship **fk specializations. to studentApplicationForms.**

##### 3.11.1 **fk specializations. to studentApplicationForms.** Diagram

<table><thead><tr><td>Parent Table</td><td>Parent field</td></tr></thead><tbody><tr><td><a href=#01333ab0-9846-11ec-a11a-61c866bfca96>specializations</a></td><td><a href=#142f0040-9846-11ec-a11a-61c866bfca96>id</a></td></tr></tbody></table>

![Hackolade image](static/image189.png?raw=true)![Hackolade image](static/image190.png?raw=true)

<table><thead><tr><td>Child Table</td><td>Child field</td></tr></thead><tbody><tr><td><a href=#86e576f0-9855-11ec-a11a-61c866bfca96>studentApplicationForms</a></td><td><a href=#68490f40-98af-11ec-a8e6-f363f79d3ea0>specId_1</a></td></tr></tbody></table>

##### 3.11.2 **fk specializations. to studentApplicationForms.** Properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>fk specializations. to studentApplicationForms.</td></tr><tr><td>Description</td><td></td></tr><tr><td>Parent Collection</td><td><a href=#01333ab0-9846-11ec-a11a-61c866bfca96>specializations</a></td></tr><tr><td>Parent field</td><td><a href=#142f0040-9846-11ec-a11a-61c866bfca96>id</a></td></tr><tr><td>Parent Cardinality</td><td>n</td></tr><tr><td>Child Collection</td><td><a href=#86e576f0-9855-11ec-a11a-61c866bfca96>studentApplicationForms</a></td></tr><tr><td>Child field</td><td><a href=#68490f40-98af-11ec-a8e6-f363f79d3ea0>specId_1</a></td></tr><tr><td>Child Cardinality</td><td>n</td></tr><tr><td>Comments</td><td></td></tr></tbody></table>

### <a id="8bf63530-98af-11ec-a8e6-f363f79d3ea0"></a>3.12 Relationship **fk specializations. to studentApplicationForms.**

##### 3.12.1 **fk specializations. to studentApplicationForms.** Diagram

<table><thead><tr><td>Parent Table</td><td>Parent field</td></tr></thead><tbody><tr><td><a href=#01333ab0-9846-11ec-a11a-61c866bfca96>specializations</a></td><td><a href=#142f0040-9846-11ec-a11a-61c866bfca96>id</a></td></tr></tbody></table>

![Hackolade image](static/image191.png?raw=true)![Hackolade image](static/image192.png?raw=true)

<table><thead><tr><td>Child Table</td><td>Child field</td></tr></thead><tbody><tr><td><a href=#86e576f0-9855-11ec-a11a-61c866bfca96>studentApplicationForms</a></td><td><a href=#81422fe0-98af-11ec-a8e6-f363f79d3ea0>specId_2</a></td></tr></tbody></table>

##### 3.12.2 **fk specializations. to studentApplicationForms.** Properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>fk specializations. to studentApplicationForms.</td></tr><tr><td>Description</td><td></td></tr><tr><td>Parent Collection</td><td><a href=#01333ab0-9846-11ec-a11a-61c866bfca96>specializations</a></td></tr><tr><td>Parent field</td><td><a href=#142f0040-9846-11ec-a11a-61c866bfca96>id</a></td></tr><tr><td>Parent Cardinality</td><td>n</td></tr><tr><td>Child Collection</td><td><a href=#86e576f0-9855-11ec-a11a-61c866bfca96>studentApplicationForms</a></td></tr><tr><td>Child field</td><td><a href=#81422fe0-98af-11ec-a8e6-f363f79d3ea0>specId_2</a></td></tr><tr><td>Child Cardinality</td><td>n</td></tr><tr><td>Comments</td><td></td></tr></tbody></table>

### <a id="949a4640-98af-11ec-a8e6-f363f79d3ea0"></a>3.13 Relationship **fk specializations. to studentApplicationForms.**

##### 3.13.1 **fk specializations. to studentApplicationForms.** Diagram

<table><thead><tr><td>Parent Table</td><td>Parent field</td></tr></thead><tbody><tr><td><a href=#01333ab0-9846-11ec-a11a-61c866bfca96>specializations</a></td><td><a href=#142f0040-9846-11ec-a11a-61c866bfca96>id</a></td></tr></tbody></table>

![Hackolade image](static/image193.png?raw=true)![Hackolade image](static/image194.png?raw=true)

<table><thead><tr><td>Child Table</td><td>Child field</td></tr></thead><tbody><tr><td><a href=#86e576f0-9855-11ec-a11a-61c866bfca96>studentApplicationForms</a></td><td><a href=#8dfe1320-98af-11ec-a8e6-f363f79d3ea0>specId_3</a></td></tr></tbody></table>

##### 3.13.2 **fk specializations. to studentApplicationForms.** Properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>fk specializations. to studentApplicationForms.</td></tr><tr><td>Description</td><td></td></tr><tr><td>Parent Collection</td><td><a href=#01333ab0-9846-11ec-a11a-61c866bfca96>specializations</a></td></tr><tr><td>Parent field</td><td><a href=#142f0040-9846-11ec-a11a-61c866bfca96>id</a></td></tr><tr><td>Parent Cardinality</td><td>n</td></tr><tr><td>Child Collection</td><td><a href=#86e576f0-9855-11ec-a11a-61c866bfca96>studentApplicationForms</a></td></tr><tr><td>Child field</td><td><a href=#8dfe1320-98af-11ec-a8e6-f363f79d3ea0>specId_3</a></td></tr><tr><td>Child Cardinality</td><td>n</td></tr><tr><td>Comments</td><td></td></tr></tbody></table>

### <a id="4362d7a0-98b0-11ec-a8e6-f363f79d3ea0"></a>3.14 Relationship **fk studentApplicationForms. to studentsPrimaryDetails.**

##### 3.14.1 **fk studentApplicationForms. to studentsPrimaryDetails.** Diagram

<table><thead><tr><td>Parent Table</td><td>Parent field</td></tr></thead><tbody><tr><td><a href=#86e576f0-9855-11ec-a11a-61c866bfca96>studentApplicationForms</a></td><td><a href=#2605b2e0-98ab-11ec-a8e6-f363f79d3ea0>applicationId</a></td></tr></tbody></table>

![Hackolade image](static/image195.png?raw=true)![Hackolade image](static/image196.png?raw=true)

<table><thead><tr><td>Child Table</td><td>Child field</td></tr></thead><tbody><tr><td><a href=#64c55110-983e-11ec-a11a-61c866bfca96>studentsPrimaryDetails</a></td><td><a href=#fc955980-984e-11ec-a11a-61c866bfca96>courseDetails.[-1].applicationID</a></td></tr></tbody></table>

##### 3.14.2 **fk studentApplicationForms. to studentsPrimaryDetails.** Properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>fk studentApplicationForms. to studentsPrimaryDetails.</td></tr><tr><td>Description</td><td></td></tr><tr><td>Parent Collection</td><td><a href=#86e576f0-9855-11ec-a11a-61c866bfca96>studentApplicationForms</a></td></tr><tr><td>Parent field</td><td><a href=#2605b2e0-98ab-11ec-a8e6-f363f79d3ea0>applicationId</a></td></tr><tr><td>Parent Cardinality</td><td>n</td></tr><tr><td>Child Collection</td><td><a href=#64c55110-983e-11ec-a11a-61c866bfca96>studentsPrimaryDetails</a></td></tr><tr><td>Child field</td><td><a href=#fc955980-984e-11ec-a11a-61c866bfca96>applicationID</a></td></tr><tr><td>Child Cardinality</td><td>1</td></tr><tr><td>Comments</td><td></td></tr></tbody></table>

### <a id="333e4030-98ab-11ec-a8e6-f363f79d3ea0"></a>3.15 Relationship **fk studentsPrimaryDetails. to studentApplicationForms.**

##### 3.15.1 **fk studentsPrimaryDetails. to studentApplicationForms.** Diagram

<table><thead><tr><td>Parent Table</td><td>Parent field</td></tr></thead><tbody><tr><td><a href=#64c55110-983e-11ec-a11a-61c866bfca96>studentsPrimaryDetails</a></td><td><a href=#2b041620-984b-11ec-a11a-61c866bfca96>id</a></td></tr></tbody></table>

![Hackolade image](static/image197.png?raw=true)![Hackolade image](static/image198.png?raw=true)
d

<table><thead><tr><td>Child Table</td><td>Child field</td></tr></thead><tbody><tr><td><a href=#86e576f0-9855-11ec-a11a-61c866bfca96>studentApplicationForms</a></td><td><a href=#2f2e8450-98ab-11ec-a8e6-f363f79d3ea0>studentId</a></td></tr></tbody></table>

##### 3.15.2 **fk studentsPrimaryDetails. to studentApplicationForms.** Properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>fk studentsPrimaryDetails. to studentApplicationForms.</td></tr><tr><td>Description</td><td></td></tr><tr><td>Parent Collection</td><td><a href=#64c55110-983e-11ec-a11a-61c866bfca96>studentsPrimaryDetails</a></td></tr><tr><td>Parent field</td><td><a href=#2b041620-984b-11ec-a11a-61c866bfca96>id</a></td></tr><tr><td>Parent Cardinality</td><td>1</td></tr><tr><td>Child Collection</td><td><a href=#86e576f0-9855-11ec-a11a-61c866bfca96>studentApplicationForms</a></td></tr><tr><td>Child field</td><td><a href=#2f2e8450-98ab-11ec-a8e6-f363f79d3ea0>studentId</a></td></tr><tr><td>Child Cardinality</td><td>n</td></tr><tr><td>Comments</td><td></td></tr></tbody></table>

### <a id="dfb77d40-9851-11ec-a11a-61c866bfca96"></a>3.16 Relationship **fk studentsPrimaryDetails. to studentSecondaryDetails.**

##### 3.16.1 **fk studentsPrimaryDetails. to studentSecondaryDetails.** Diagram

<table><thead><tr><td>Parent Table</td><td>Parent field</td></tr></thead><tbody><tr><td><a href=#64c55110-983e-11ec-a11a-61c866bfca96>studentsPrimaryDetails</a></td><td><a href=#2b041620-984b-11ec-a11a-61c866bfca96>id</a></td></tr></tbody></table>

![Hackolade image](static/image199.png?raw=true)![Hackolade image](static/image200.png?raw=true)

<table><thead><tr><td>Child Table</td><td>Child field</td></tr></thead><tbody><tr><td><a href=#d9a1d4b0-9850-11ec-a11a-61c866bfca96>studentSecondaryDetails</a></td><td><a href=#92e38540-9851-11ec-a11a-61c866bfca96>studentID</a></td></tr></tbody></table>

##### 3.16.2 **fk studentsPrimaryDetails. to studentSecondaryDetails.** Properties

<table><thead><tr><td>Property</td><td>Value</td></tr></thead><tbody><tr><td>Name</td><td>fk studentsPrimaryDetails. to studentSecondaryDetails.</td></tr><tr><td>Description</td><td></td></tr><tr><td>Parent Collection</td><td><a href=#64c55110-983e-11ec-a11a-61c866bfca96>studentsPrimaryDetails</a></td></tr><tr><td>Parent field</td><td><a href=#2b041620-984b-11ec-a11a-61c866bfca96>id</a></td></tr><tr><td>Parent Cardinality</td><td>1</td></tr><tr><td>Child Collection</td><td><a href=#d9a1d4b0-9850-11ec-a11a-61c866bfca96>studentSecondaryDetails</a></td></tr><tr><td>Child field</td><td><a href=#92e38540-9851-11ec-a11a-61c866bfca96>studentID</a></td></tr><tr><td>Child Cardinality</td><td>1</td></tr><tr><td>Comments</td><td></td></tr></tbody></table>

### <a id="edges"></a>