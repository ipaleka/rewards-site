# ASA Stats Rewards Site

[![build-status](https://github.com/asastats/rewards-site/actions/workflows/build.yml/badge.svg)](https://github.com/asastats/rewards-site/actions/workflows/build.yml) [![docs](https://app.readthedocs.org/projects/rewards-site/badge/?version=latest)](https://rewards-site.readthedocs.io/en/latest/?badge=latest) [![codecov](https://codecov.io/gh/asastats/rewards-site/graph/badge.svg?token=DQC4SRY8J9)](https://codecov.io/gh/asastats/rewards-site) ![ansible-lint](https://github.com//asastats/rewards-site/actions/workflows/ansible-lint.yml/badge.svg) ![molecule](https://github.com/asastats/rewards-site/actions/workflows/molecule.yml/badge.svg) 

A website dedicated to ASA Stats contributions. Previously written in Laravel, now powered by Django.

## Usage

It provides a preview for all historic and latest contributions, hot tasks, contributions guide and more. Community members can use our [Discord Bot](https://github.com/asastats/rewards-site/tree/main/rewardsweb/rewardsbot) to suggest rewards for contributions which appear on this website.

> [!IMPORTANT]
> In order for the bot to access all the channels in the ASA Stats Discord, an admin has to assign it the `Verified` role.

### Environment variables

Environment variables shouldn't reside in repository, so `.env` file with the following content has to be created in the `rewards-site/rewardsweb` directory:

```
SECRET_KEY=mysecretkey
DATABASE_NAME=rewards_db
DATABASE_USER=rewards_user
DATABASE_PASSWORD=mypassword
GITHUB_BOT_CLIENT_ID=111111111
GITHUB_BOT_PRIVATE_KEY_FILENAME=rewards-bot.private-key.pem
GITHUB_BOT_INSTALLATION_ID=111111111
INITIAL_SUPERUSERS=username1,username2
INITIAL_SUPERUSER_ADDRESSES=SUPERUSER1ADDRESS,SUPERUSER2ADDRESS
INITIAL_SUPERUSER_PASSWORDS=password1,password2
```

## Goals

- Stimulate community engagement 
- Provide a nice contributions overview
- Make the process of suggesting and collecting rewards straightforward
- Have a nice overview and documentation of contribution/reward process

## Roadmap

- [x] Initialize Django project on this repository
- [x] Setup environment: docker (optional), database, env file(s)
- [x] Create data models and migrations
- [x] Adjustment of script for contributions spreadsheet parsing
- [x] Create script for seeding the database with parsed data
- [x] Create API routes
- [x] Create methods for managing http requests and bind them to API routes
- [x] Automated documentation building and publishing on Read The Docs platform
- [x] Create methods for CRUD operations
- [x] Implement authentication by connecting a wallet
- [x] Create deploy workflow
- [ ] Create smart contract for rewards allocation and claiming
- [ ] Develop UI for rewards allocation and claiming
- [ ] Setup a server and deploy the application
