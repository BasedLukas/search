# GetDelv landing site

Product landing page built with static HTML, CSS, JavaScript and Vite.

- `index.html`: page content and illustrative API/MCP examples.
- `assets/`: styles and JavaScript; `public/`: site icons and metadata.
- `design/`: an alternate page layout and styles.

Run from this directory:

```sh
npm ci
npm run dev
npm run build
```

The build writes to `dist/`; `npm run preview` serves that build. Search and MCP integration code lives in [search_app_delv](../search_app_delv/), [search_delv](../search_delv/) and [mcp_delv](../mcp_delv/).
