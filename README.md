# ASA Stats Rewards Site

A website dedicated to ASA Stats contributions. Previously written in Laravel, now powered by Django.

## Usage

It provides a preview for all historic and latest contributions, hot tasks, contributions guide and more. Community members can use our [Discord Bot](url) to suggest rewards for contributions which appear on this website.

### Environment variables

Environment variables shouldn't reside in repository, so `.env` file with the following content has to be created in the `rewards-site/rewardsweb` directory:

```
SECRET_KEY="mysecretkey"
DATABASE_NAME="rewards_db"
DATABASE_USER="rewards_user"
DATABASE_PASSWORD="mypassword"
PGPASSFILE="/home/{username}/.pgpass"
```

## Goals

- Stimulate community engagement 
- Provide a nice contributions overview
- Make the process of suggesting and collecting rewards straightforward
- Have a nice overview and documentation of contribution/reward process

## Roadmap

- [ ] Initialize Django project on this repository
- [ ] Setup environment: docker (optional), database, env file(s)
- [ ] Create data models and migrations
- [ ] Adjustment of script for contributions spreadsheet parsing
- [ ] Create script for seeding the database with parsed data
- [ ] Add API authentication
- [ ] Create API routes
- [ ] Create methods for managing http requests and bind them to API routes
- [ ] Create methods for CRUD operations
- [ ] Create deploy workflow
- [ ] Setup a server and deploy the application
