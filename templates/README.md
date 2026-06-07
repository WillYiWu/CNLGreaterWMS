# wms templates (templates)

wms templates

## Install the dependencies
```bash
yarn
```

## Configure the API URL

The frontend uses the current page origin by default. This is the normal
production setup when the frontend and API share one domain.

For local development with the API on a different origin, create the ignored
local configuration file:

```bash
cp public/statics/baseurl.example.txt public/statics/baseurl.txt
```

Set `public/statics/baseurl.txt` to the API origin, without a trailing slash.
For example:

```text
http://127.0.0.1:8000
```

### Start the app in development mode (hot-code reloading, error reporting, etc.)
```bash
quasar dev
```

### Lint the files
```bash
yarn run lint
```

### Build the app for production
```bash
quasar build
```

### Customize the configuration
See [Configuring quasar.conf.js](https://quasar.dev/quasar-cli/quasar-conf-js).
