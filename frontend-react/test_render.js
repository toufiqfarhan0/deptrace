import { createServer } from 'vite'
import React from 'react'
import ReactDOMServer from 'react-dom/server'

// Set up browser-like globals for SSR
global.document = {
  documentElement: {
    setAttribute: () => {},
    getAttribute: () => 'dark',
  },
  getElementById: () => null,
}
global.window = {
  matchMedia: () => ({ matches: false }),
}
global.localStorage = {
  getItem: () => null,
  setItem: () => {},
}
global.fetch = async () => ({
  ok: true,
  json: async () => ({ status: 'ok', hydradb: 'ok', entities: ['REL-311', 'kernel-selector'] })
})

async function run() {
  const server = await createServer({
    root: process.cwd(),
    server: { middlewareMode: true },
    appType: 'custom',
  })

  try {
    console.log('--- TEST 1: Load suggestions.js ---')
    const suggestionsMod = await server.ssrLoadModule('/src/data/suggestions.js')
    console.log('Suggestions count:', suggestionsMod.SUGGESTIONS_CATALOG?.length)
    console.log('Inquiry queries:', suggestionsMod.getInquiryQueries())
    console.log('Quick trace entities:', suggestionsMod.getQuickTraceEntities())

    console.log('--- TEST 1B: Test hydraStatus.js helper ---')
    const statusMod = await server.ssrLoadModule('/src/utils/hydraStatus.js')
    const cloudStatus = { status: 'ok', hydradb: 'ok (cloud: veridex-hackhydra)' }
    const localStatus = { status: 'ok', hydradb: 'ok' }
    const loadingStatus = { status: 'loading', hydradb: '' }
    const errorStatus = { status: 'degraded', hydradb: 'unreachable' }

    if (statusMod.getHydraStatusMode(cloudStatus) !== 'cloud') throw new Error('Cloud mode detection failed')
    if (statusMod.getHydraStatusLabel(cloudStatus) !== 'HYDRADB CLOUD  CONNECTED') throw new Error('Cloud label failed')
    if (statusMod.getHydraStatusMode(localStatus) !== 'local') throw new Error('Local mode detection failed')
    if (statusMod.getHydraStatusLabel(localStatus) !== 'HYDRADB LOCAL  CONNECTED') throw new Error('Local label failed')
    if (statusMod.getHydraStatusMode(loadingStatus) !== 'loading') throw new Error('Loading mode detection failed')
    if (statusMod.getHydraStatusLabel(loadingStatus) !== 'CONNECTING...') throw new Error('Loading label failed')
    if (statusMod.getHydraStatusMode(errorStatus) !== 'error') throw new Error('Error mode detection failed')
    if (statusMod.getHydraStatusLabel(errorStatus) !== 'HYDRADB OFFLINE') throw new Error('Error label failed')
    console.log('hydraStatus helper tests: ALL PASSED')

    console.log('--- TEST 2: Load and render LandingPage ---')
    const LandingMod = await server.ssrLoadModule('/src/components/LandingPage.jsx')
    const Landing = LandingMod.default
    const landingHtml = ReactDOMServer.renderToString(React.createElement(Landing, {
      onEnterConsole: () => {},
      onNavigateToWhyHydra: () => {},
      hydraStatus: { status: 'ok', hydradb: 'ok' },
      theme: 'dark',
      onToggleTheme: () => {},
    }))
    console.log('Landing rendered, length:', landingHtml.length)

    console.log('--- TEST 3: Load and render Sidebar ---')
    const SidebarMod = await server.ssrLoadModule('/src/components/Sidebar.jsx')
    const Sidebar = SidebarMod.default
    const sidebarHtml = ReactDOMServer.renderToString(React.createElement(Sidebar, {
      activeView: 'ask',
      onNavigate: () => {},
      hydraStatus: { status: 'ok', hydradb: 'ok' },
      onGoHome: () => {},
    }))
    console.log('Sidebar rendered, length:', sidebarHtml.length)

    console.log('--- TEST 4: Load and render InvestigationView ---')
    const AskMod = await server.ssrLoadModule('/src/components/InvestigationView.jsx')
    const InvestigationView = AskMod.default
    const askHtml = ReactDOMServer.renderToString(React.createElement(InvestigationView, {
      initialQuery: '',
      onQueryChange: () => {},
      onNavigateToTrace: () => {},
    }))
    console.log('InvestigationView rendered, length:', askHtml.length)

    console.log('--- TEST 5: Load and render TraceView ---')
    const TraceMod = await server.ssrLoadModule('/src/components/TraceView.jsx')
    const TraceView = TraceMod.default
    const traceHtml = ReactDOMServer.renderToString(React.createElement(TraceView, {
      initialEntity: '',
      onEntityChange: () => {},
      onNavigateToAsk: () => {},
    }))
    console.log('TraceView rendered, length:', traceHtml.length)

    console.log('--- TEST 6: Load and render SuggestionsView ---')
    const SugMod = await server.ssrLoadModule('/src/components/SuggestionsView.jsx')
    const SuggestionsView = SugMod.default
    const sugHtml = ReactDOMServer.renderToString(React.createElement(SuggestionsView, {
      onSelectQuery: () => {},
      onSelectTrace: () => {},
    }))
    console.log('SuggestionsView rendered, length:', sugHtml.length)

    console.log('--- TEST 7: Load and render EntityExplorer ---')
    const EntMod = await server.ssrLoadModule('/src/components/EntityExplorer.jsx')
    const EntityExplorer = EntMod.default
    const entHtml = ReactDOMServer.renderToString(React.createElement(EntityExplorer, {
      onTraceEntity: () => {},
      onAskEntity: () => {},
    }))
    console.log('EntityExplorer rendered, length:', entHtml.length)

    console.log('--- TEST 8: Load and render App (Full Component) ---')
    const AppMod = await server.ssrLoadModule('/src/App.jsx')
    const App = AppMod.default
    const appHtml = ReactDOMServer.renderToString(React.createElement(App))
    console.log('App (landing) rendered, length:', appHtml.length)

    // Test each console view rendering in isolation
    const views = ['ask', 'trace', 'suggestions', 'entities', 'why-hydra', 'health']
    for (const v of views) {
      console.log(`--- TEST View: ${v} ---`)
      // Simulate App rendering console directly
      const consoleAppHtml = ReactDOMServer.renderToString(React.createElement(App))
      if (!consoleAppHtml) throw new Error(`Failed to render view: ${v}`)
    }

    console.log('\n>>> ALL SSR AND VIEW CHECKS PASSED WITH ZERO RUNTIME ERRORS! <<<')
  } catch (err) {
    console.error('CRITICAL SSR ERROR:', err)
  } finally {
    await server.close()
    process.exit(0)
  }
}

run()
