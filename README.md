# State-owned ASes dataset

Welcome to the state-owned ASes dataset repository. Here you can find a dataset containing a list of _ASes of State-Owned Internet Operators_.

The list of _ASes of State-Owned Internet Operators_ is a product of the research published in the paper _"Identifying ASes of State-owned Internet operators"_ appearing in the Proceedings of the ACM Internet Measurement Conference (IMC) 2021, November 2021, Virtual Event.

## Table of Contents

1. [State-owned ASes dataset](#dataset)
   1. [Data structure](#dataset_data_structure)
   2. [Data formats](#dataset_data_formats)
   3. [Minority state-owned providers](#dataset_minority_state-owned)
2. [Examples](#examples)
3. [Citation](#citation)

## Repo structure

```
.
├── LICENSE
├── README.md
├── data
│   ├── minority-state-owned-ases
│   │   ├── csv
│   │   │   ├── minority_state_owned_ases.csv
│   │   │   ├── minority_state_owned_ases_table_ases.csv
│   │   │   └── minority_state_owned_ases_table_organizations.csv
│   │   ├── json
│   │   │   ├── minority_state_owned_ases_table_ases.json
│   │   │   └── minority_state_owned_ases_table_organizations.json
│   │   └── sqlite
│   │       └── minority_state_owned_ases.sqlite
│   └── state-owned-ases
│       ├── csv
│       │   ├── state_owned_ases.csv
│       │   ├── state_owned_ases_table_ases.csv
│       │   └── state_owned_ases_table_organizations.csv
│       ├── json
│       │   ├── state_owned_ases_table_ases.json
│       │   └── state_owned_ases_table_organizations.json
│       └── sqlite
│           └── state_owned_ases.sqlite
├── examples
│   ├── minority-state-owned-ases
│   │   ├── load_from_json.ipynb
│   │   ├── load_from_organizations_and_ases_csv_files.ipynb
│   │   ├── load_from_single_table_csv_file.ipynb
│   │   └── load_from_sqlite.ipynb
│   └── state-owned-ases
│       ├── load_from_json.ipynb
│       ├── load_from_organizations_and_ases_csv_files.ipynb
│       ├── load_from_single_table_csv_file.ipynb
│       └── load_from_sqlite.ipynb
└── requirements.txt

12 directories, 23 files
```

# <a name="dataset"></a>1. Datasets and data formats

In this repository, we provide two datasets:

1. _(Main dataset)_ A list examined in-depth of ASes operated by state-owned Internet providers.
2. _(Additional dataset)_ A preliminary and partial list of ASes operated by minority state-owned Internet providers.

<!-- ## 1.1 List of ASes operated by state-owned providers -->

We provide the datasets of state-owned ASes in three formats **CSV**, **JSON** and **sqlite**

## <a name="dataset_data_structure"></a>1.1. Data structure

We use the following example to illustrate the data structure of the records in our dataset.

```
# Ownership details of an identified
# state-owned organization
{
  "conglomerate_name": "NO-TELENOR",
  "org_id": "ORG-NA38-RIPE",
  "org_name": "Telenor Norge AS",
  "ownership_cc": "NO",
  "ownership_country_name": "Norway",
  "rir": "RIPE",
  "source": "Company's website",
  "quote": "Major Shareholdings: Government of Norway (54,7%)",
  "quote_lang": "English",
  "url":"https://www.telenor.com/investors/share-information/major-shareholdings"
  "additional_info": "",
  "inputs": [G, E, W, O],
  "parent_org":,
  "target_cc":,
  "target_country_name":,
}
# List of ASes operated by the identified
# state-owned organization
{
  "org_id": "ORG-NA38-RIPE",
  "asn": [2119, 8210, 8394, 8786, 39197, 197943, 200168]
}
```

Our dataset is composed of two data entities ```organization``` and ```ases``` which are linked by the key ```org_id```. Next, we describe each of the fields in both entities.

**Organization**

- ```conglomerate_name```: name of the conglomerate the company belongs to.
- ```org_id```: Org ID from CAIDA's AS2Org.
- ```org_name```: The name of the organization according to CAIDA's AS2Org records.
- ```ownership_cc```: ISO-3361 country code.
- ```ownership_country_name```: country name.
- ```rir```: country's RIR.
- ```source```: Type of confirmation sources that validated the inference.
- ```quote```: The exact quote we use to determine the state
ownership.
- ```quote_lang```: Language of the quote.
- ```url```: the URL to the confirmation data source.
- ```additional_info```: _(optional)_ In some cases, this record adds some details to understand the state ownership _(e.g., specifying that a hedge fund is state-owned)_
- ```inputs```: The input data source(s) that caused this organization to be initially added to the candidate list (the associated research paper describes candidate lists). We abbreviate the input sources using the following convention:
  - **G**: Country-level AS geolocation.
  - **E**: APNIC eyeballs dataset.
  - **C**: Country-Level Transit Influence.
  - **O**: Orbis.
  - **W**: Wikipedia \& Freedom House.
- ```parent_org```: _(optional, only for foreign subsidiaries)_ the parent company's Org ID
- ```target_cc```: _(optional, only for foreign subsidiaries)_ The ISO-3361 country code where the company is intended to operate.
- ```target_country_name```: _(optional, only for foreign subsidiaries)_ The name of the country where the company is intended to operate.

**ASes**

- ```org_id```: CAIDA AS2Org's Org ID
- ```asn```: Autonomous System Number associated with that ```org_id```

<span style="color:red">*Minority state-owned Internet providers*</span>. In the dataset of the minority state-owned ASes we include one additional field ```onwership_percentage``` to ```organizations``` to indicate the state ownership in the company operating the Autonomous System

## <a name="dataset_data_formats"></a>1.2. Data formats

#### CSV files

We provide **two alternatives** to access the dataset using CSV files.

1. **Single-table file**: Some users of our dataset might prefer to have all the information in a single file.
  - The list of state-owned ASes is here ([single-file state-owned ASes dataset](data/state-owned-ases/csv/state_owned_ases.csv))!
  - The preliminary and partial list of _minority_ state-owned ASes is here ([single-file **minority** state-owned ASes dataset](data/minority-state-owned-ases/csv/minority_state_owned_ases.csv))!
2. **Organizations and ASes files**: Following the data structure we described above, CSV files containing Organizations and ASes are available here:
  - state-owned ASes ([Orgs](data/state-owned-ases/csv/state_owned_ases_table_organizations.csv)) and ([ASes](data/state-owned-ases/csv/state_owned_ases_table_ases.csv)).
  - The preliminary and partial list of _minority_ state-owned ASes ([Orgs](data/minority-state-owned-ases/csv/minority_state_owned_ases_table_organizations.csv)) and([ASes](data/minority-state-owned-ases/csv/minority_state_owned_ases_table_ases.csv)).

#### JSON files

As described in the [Data structure](#dataset:data-structure) example, Organization and ASes JSON files are available here:
- state-owned ASes ([Orgs](data/state-owned-ases/json/state_owned_ases_table_organizations.json)) and ([ASes](data/state-owned-ases/json/state_owned_ases_table_ases.json)).
- The preliminary and partial list of _minority_ state-owned ASes ([Orgs](data/minority-state-owned-ases/json/minority_state_owned_ases_table_organizations.json)) and ([ASes](data/minority-state-owned-ases/json/minority_state_owned_ases_table_ases.json)).

#### sqlite database


We also provide access to the dataset using sqlite. We provide two separate databases for clarity. The first database includes the list of state-owned Ases. The second databases includes the preliminary and partial list of minority state-owned ASes. These databases include two tables each, ```organizations``` and ```ases```. The files containing the sqlite databases are located here:
- state-owned ASes ([sqlite database](data/state-owned-ases/sqlite/state_owned_ases.sqlite))
- The preliminary and partial list of _minority_ state-owned ASes ([sqlite database](data/minority-state-owned-ases/sqlite/minority_state_owned_ases.sqlite))

## <a name="dataset_minority_state-owned"></a>1.3. Description of the list of minority state-owned providers

Identifying ASes operated by minority state-owned Internet Operators was beyond the scope of this project. However, during our manual examination we discovered some ASes with partial state ownership, that is where the state directly or indirectly owns less than 50% of the company's shares. We share this additional outcome of our research but acknowledge its limitations.

**Completeness** We did not systematically look for minority state-owned Internet Operators, since they were beyond the scope of the process. As a result, the coverage of this list is unknown, although we assume that the list is very incomplete.

**Depth** We did not investigate the parent-child structure of minority state-owned companies. Therefore, we do not list subsidiaries of the companies in this list. There are some prominent examples of large companies (that may have many subsidiaries) in our list such as Orange (AS5511, [PeeringDB entry](https://www.peeringdb.com/net/495)), Deustche Telekom (AS3320, [PeeringDB entry](https://www.peeringdb.com/net/196)) and NTT DoCoMo(AS9605, [PeeringDB entry](https://www.peeringdb.com/net/2697)). We are aware that these minority state-owned companies have a large international footprint, but their identification was incidental to our main goal of identifying _majority_ state-owned companies.

# <a name="examples"></a>2. Examples

To get familiar with the datasets, we include on this repo **four** Jupyter Notebooks for both datasets. We use Python on these notebooks to also provide methods that enable loading and interacting with the dataset. These examples are here:

1. State-Owned ASes
   1. [Load single-table file](examples/state-owned-ases/load_from_single_table_csv_file.ipynb)
   2. [Load Organizations and ASes CSV files](examples/state-owned-ases/load_from_organizations_and_ases_csv_files.ipynb)
   3. [Load from JSON](examples/state-owned-ases/load_from_json.ipynb)
   4. [Fetch data from sqlite database](examples/state-owned-ases/load_from_sqlite.ipynb)
2. Minority State-Owned ASes
   1. [Load single-table file](examples/minority-state-owned-ases/load_from_single_table_csv_file.ipynb)
   2. [Load Organizations and ASes CSV files](examples/minority-state-owned-ases/load_from_organizations_and_ases_csv_files.ipynb)
   3. [Load from JSON](examples/minority-state-owned-ases/load_from_json.ipynb)
   4. [Fetch data from sqlite database](examples/minority-state-owned-ases/load_from_sqlite.ipynb)

## (Optional) setup for running these examples

We highly recommend you to use a Python virtual environment to run these examples. In this repository, we also include a ```requirements.txt``` to install all python packages needed to run the examples.


To install this virtual environment, you have to run the following commands

```
$ python3 -m venv .state-owned-ases
$ source .state-owned-ases/bin/activate
$ pip3 install ipykernel
$ ipython kernel install --user --name=.state-owned-ases
$ pip3 install -r requirements.txt
```



# <a name="citation"></a>3. Citation

If you use our dataset, please cite it as:

```
```
