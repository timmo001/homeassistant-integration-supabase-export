# Home Assistant Integration - Supabase Export

This integration allows you to export data from Home Assistant to a Supabase database.

## Installation

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=timmo001&repository=homeassistant-integration-supabase-export&category=integration)

This integration is available in the [Home Assistant Community Store](https://hacs.xyz/).

## Setup

1. Create a Supabase project and database.
1. Run the following SQL query to create the required tables:

```sql
create table homeassistant_entities (
  id bigint not null primary key,
  created_at timestamp default now(),
  entity_id text not null,
  state text,
  attributes json,
  last_changed timestamp default now()
);

create table homeassistant_metadata (
  id bigint not null primary key,
  created_at timestamp default now(),
  provisioned boolean,
  data json
);
```

## Configuration

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=supabase_export)

You can configure the integration via the Home Assistant UI.

### Options

Once the integration is configured, you should then configure the options for the integration. This can be done via the Home Assistant UI.

From here, you can configure the following options:

- **Update interval**: The interval at which the integration will update the data in the database. This is in seconds.
- **Entities**: The entities that you want to export to the database.
