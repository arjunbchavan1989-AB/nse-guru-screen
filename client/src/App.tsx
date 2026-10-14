import { useEffect, useMemo, useState } from "react";
import { ArrowDown, ArrowDownUp, ArrowRight, ArrowUpRight, Check, CheckCheck, ChevronLeft, ChevronRight, Clipboard, Download, ExternalLink, Filter, GitBranch, Grid2X2, Info, Layers3, ListFilter, Menu, Moon, RefreshCw, Search, Settings2, ShieldCheck, SlidersHorizontal, Sun, Table2, X } from "lucide-react";
import { ResponsiveContainer, ComposedChart, Line, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";
import type { Snapshot, Stock, ScanDefinition, ScanId, Gate } from "@shared/schema";

const REPO = "https://github.com/arjunbchavan1989-AB/nse-guru-screen";
const RAW = "https://raw.githubusercontent.com/arjunbchavan1989-AB/nse-guru-screen/main/client/public/data/";
const money = (n: number) => new Intl.NumberFormat("en-IN", {maximumFractionDigits:2}).format(n);
const num = (n: number | null | undefined, d=1) => n==null ? "—" : n.toFixed(d);
const signed = (n: number) => `${n>=0?"+":""}${n.toFixed(2)}%`;
const activeScans = (r: Stock, original: boolean) => original ? r.matches_original : r.matches;
const groups = ["Qullamaggie", "Oliver Kell", "Stockbee", "William O'Neil", "Steve Jacobs", "TraderLion"];
const abbreviations: Record<string,string> = {q_breakout:"QB",q_ep:"QE",kell:"OK",sb4:"4%",sb8:"8M",canslim:"CS",club97:"97",launchpad:"LP",htf:"HTF"};
const svgLogo = <svg viewBox="0 0 32 32" fill="none" aria-label="Guru Screen" className="logo"><path d="M3 25V12h6v13M13 25V6h6v19M23 25V15h6v10" stroke="currentColor" strokeWidth="2.5"/><path d="m3 8 9-5 9 7 8-6" stroke="currentColor" strokeWidth="2.5" strokeLinejoin="round"/></svg>;

function App(){
  const [data,setData]=useState<Snapshot|null>(null), [error,setError]=useState("");
  const [loading,setLoading]=useState(true), [refreshing,setRefreshing]=useState(false);
  const [feed,setFeed]=useState<"github"|"bundled">("bundled");
  const [sessions,setSessions]=useState<string[]>([]), [session,setSession]=useState("latest");
  const [view,setView]=useState<"board"|"matrix">("board");
  const [page,setPage]=useState<"scanner"|"rules"|"health">("scanner");
  const [scan,setScan]=useState<string>("all"), [search,setSearch]=useState("");
  const [sort,setSort]=useState("matches"),[minimum,setMinimum]=useState(2);
  const [original,setOriginal]=useState(false),[onlyMulti,setOnlyMulti]=useState(false);
  const [showAll,setShowAll]=useState(false),[sideOpen,setSideOpen]=useState(false);
  const [selected,setSelected]=useState<Stock|null>(null),[ruleScan,setRuleScan]=useState("q_breakout");
  const [dark,setDark]=useState(()=>window.matchMedia("(prefers-color-scheme: dark)").matches);
  const [message,setMessage]=useState(""),[copied,setCopied]=useState("");
  const [bars,setBars]=useState<any[]>([]),[chartError,setChartError]=useState("");
  const [chartLoading,setChartLoading]=useState(false);

  useEffect(()=>{document.documentElement.dataset.theme=dark?"dark":"light"},[dark]);
  async function load(which="latest",manual=false){
    manual?setRefreshing(true):setLoading(true);setError("");
    const file=which==="latest"?"latest.json":`history/${which}.json`;
    const key=Math.floor(Date.now()/60000);
    let loaded:Snapshot|null=null;
    try{
      const response=await fetch(`${RAW}${file}?v=${key}`,{cache:"no-store"});
      if(!response.ok)throw Error("GitHub feed unavailable");
      const payload=await response.json();
      if(payload.schema_version!==1 || !Array.isArray(payload.rows) || payload.market_data?.bootstrap)throw Error("Independent GitHub acquisition not ready");
      loaded=payload;setFeed("github");
    }catch{
      try{
        const response=await fetch(`./data/${file}?v=${key}`,{cache:"no-store"});
        if(!response.ok)throw Error("No saved snapshot for this session");
        loaded=await response.json();setFeed("bundled");
      }catch(err:any){setError(err.message||"Unable to load daily snapshot");}
    }
    if(loaded){setData(loaded);setSelected(null);}
    setLoading(false);setRefreshing(false);
    if(manual)setMessage(loaded?`Loaded verified session ${loaded.last_trading_date}. This refresh reads published data; it does not start the GitHub scan.`:"Could not refresh. Last visible snapshot retained.");
  }
  useEffect(()=>{
    load();
    fetch(`${RAW}sessions.json?v=${Math.floor(Date.now()/60000)}`).then(r=>r.ok?r.json():Promise.reject()).then(setSessions)
      .catch(()=>fetch("./data/sessions.json").then(r=>r.json()).then(setSessions).catch(()=>{}));
    const timer=setInterval(()=>{load("latest",true)},5*60*1000);
    return()=>clearInterval(timer);
  },[]);
  useEffect(()=>{
    if(!message)return;const timer=setTimeout(()=>setMessage(""),7000);return()=>clearTimeout(timer);
  },[message]);
  useEffect(()=>{
    if(!selected)return;
    let cancelled=false;setBars([]);setChartError("");setChartLoading(true);
    async function readChart(){
      try{
        const base=feed==="github"?RAW:"./data/";
        // Never combine an archived session with a current-session chart.
        if(selected!.date!==data?.last_trading_date || session!=="latest"){
          setChartError("Historical chart not bundled for archived sessions. Open TradingView to review this date.");return;
        }
        const response=await fetch(`${base}charts/${encodeURIComponent(selected!.symbol)}.json?v=${Math.floor(Date.now()/60000)}`);
        if(!response.ok)throw Error("Chart unavailable");
        const chart=await response.json();
        if(chart.date!==selected!.date)throw Error("Chart/session mismatch; chart hidden");
        let e10=0,e20=0;
        const series=chart.bars.map((b:any,i:number)=>{
          e10=i?e10+2/11*(b.c-e10):b.c;e20=i?e20+2/21*(b.c-e20):b.c;
          return {...b,e10,e20};
        });
        if(!cancelled)setBars(series.slice(-100));
      }catch(err:any){if(!cancelled)setChartError(err.message)}
      finally{if(!cancelled)setChartLoading(false)}
    }
    readChart();
    const onKey=(e:KeyboardEvent)=>{if(e.key==="Escape")setSelected(null)};
    document.addEventListener("keydown",onKey);
    return()=>{cancelled=true;document.removeEventListener("keydown",onKey)};
  },[selected]);
  const rows=useMemo(()=>{
    if(!data)return[];
    const query=search.trim().toUpperCase();
    const list=data.rows.filter(r=>{
      const matches=activeScans(r,original);
      return (!query || r.symbol.includes(query) || r.name.toUpperCase().includes(query)) &&
        (!onlyMulti || matches.length>=minimum) &&
        (scan==="all" || scan==="multi" && matches.length>=minimum || matches.includes(scan as ScanId));
    });
    return list.sort((a,b)=>{
      if(sort==="change")return b.change_pct-a.change_pct;
      if(sort==="rvol")return b.rvol-a.rvol;
      if(sort==="rs")return (b.rs_3m??-1)-(a.rs_3m??-1);
      if(sort==="symbol")return a.symbol.localeCompare(b.symbol);
      return activeScans(b,original).length-activeScans(a,original).length || b.change_pct-a.change_pct;
    });
  },[data,search,onlyMulti,minimum,sort,scan,original]);
  const counts=useMemo(()=>Object.fromEntries((data?.scans||[]).map(s=>[s.id,data!.rows.filter(r=>activeScans(r,original).includes(s.id)).length])),[data,original]);
  const multi=data?.rows.filter(r=>activeScans(r,original).length>=minimum).length||0;
  const matched=data?.rows.filter(r=>activeScans(r,original).length).length||0;
  const matrixRows=showAll?rows:rows.filter(r=>activeScans(r,original).length);
  const visibleScans=data?.scans.filter(s=>scan==="all"||scan==="multi"||scan===s.id)||[];
  function navigate(next:string){
    setScan(next);setPage("scanner");setSideOpen(false);
  }
  async function copy(list:Stock[],key:string){
    const tickers=Array.from(new Set(list.map(r=>`NSE:${r.symbol}`))).join(",");
    if(!tickers){setMessage("No matching symbols to copy in this column.");return}
    try{
      if(navigator.clipboard?.writeText)await navigator.clipboard.writeText(tickers);
      else throw Error("Clipboard API unavailable");
      setCopied(key);setMessage(`Copied ${list.length} NSE symbols. Paste into TradingView's watchlist import.`);
      setTimeout(()=>setCopied(""),2500);
    }catch{
      // Explicit, selectable fallback works when an embedded browser blocks clipboard access.
      setMessage("Clipboard permission blocked. Select and copy the symbols below.");
      const field=document.getElementById("copy-fallback") as HTMLTextAreaElement;
      field.value=tickers;field.hidden=false;field.focus();field.select();
    }
  }
  function exportCSV(){
    const list=view==="matrix"?matrixRows:rows.filter(r=>activeScans(r,original).length);
    const quote=(value:any)=>`"${String(value??"").replaceAll('"','""')}"`;
    const headers=["Symbol","Company","Session","Close","Change %","RVOL","Scan count","Matched scans","Kell phase","RS day","RS week","RS month","RS 3M","Market cap Cr","Catalyst"];
    const csv=[headers,...list.map(r=>[r.symbol,r.name,r.date,r.close,r.change_pct,r.rvol,activeScans(r,original).length,activeScans(r,original).join(";"),r.phase,r.rs_day,r.rs_week,r.rs_month,r.rs_3m,r.market_cap_cr,r.catalyst])].map(line=>line.map(quote).join(",")).join("\r\n");
    const a=document.createElement("a");a.href=URL.createObjectURL(new Blob(["\uFEFF"+csv],{type:"text/csv;charset=utf-8"}));a.download=`guru-screen-${data?.last_trading_date}.csv`;a.click();URL.revokeObjectURL(a.href);setMessage(`Exported ${list.length} stocks to CSV.`);
  }
  const chooseRule=(id:string)=>{setRuleScan(id);setPage("rules")};
  const selectedRule=data?.scans.find(s=>s.id===ruleScan);
  const selectedMatches=selected?activeScans(selected,original):[];
  return <div className="app-shell">
    <a href="#main" className="skip-link">Skip to scanner</a>
    <aside className={`sidebar ${sideOpen?"open":""}`}>
      <a className="brand" href="#main" onClick={()=>navigate("all")}>{svgLogo}<span>guru<span className="brand-light">screen</span><small>INDIA / END OF DAY</small></span></a>
      <div className="workspace"><span className="workspace-mark">IN</span><div>NSE Equity Universe<small>Growth & momentum</small></div><span className="tiny-dot"/></div>
      <div className="nav-label">WORKSPACE</div>
      <button className={`nav-item ${page==="scanner"&&scan==="all"?"active":""}`} onClick={()=>navigate("all")}><Grid2X2 size={17}/>All guru scans<span className="nav-count">9</span></button>
      <button className={`nav-item ${page==="scanner"&&scan==="multi"?"active":""}`} onClick={()=>navigate("multi")}><Layers3 size={17}/>Multi-scan overlap<span className="nav-count">{multi}</span></button>
      <div className="nav-label nav-divider">THE GURUS</div>
      {groups.map(group=><div className="guru-group" key={group}><div className="guru-label">{group==="William O'Neil"?"O'Neil":group}</div>
        {data?.scans.filter(s=>s.guru===group).map(s=><button key={s.id} className={`nav-item child ${scan===s.id&&page==="scanner"?"active":""}`} onClick={()=>navigate(s.id)}>
          <span className="scan-dot"/>{s.name.replace(s.guru+" ","").replace("Qullamaggie ","").replace("TraderLion ","").replace("Stockbee ","").replace("O'Neil ","").replace("8 Million EP Hunt","8M EP Hunt").replace("High Tight Flag","High Tight Flag") }<span className="nav-count">{counts[s.id]??"—"}</span></button>)}
      </div>)}
      <div className="sidebar-bottom">
        <button className={`nav-item ${page==="rules"?"active":""}`} onClick={()=>{setPage("rules");setSideOpen(false)}}><SlidersHorizontal size={17}/>Scan methodology</button>
        <button className={`nav-item ${page==="health"?"active":""}`} onClick={()=>{setPage("health");setSideOpen(false)}}><ShieldCheck size={17}/>Data & automation</button>
        <a href={`${REPO}/actions`} target="_blank" rel="noreferrer" className="schedule-card"><span className="tiny-dot"/>Daily refresh <strong>19:30 IST</strong><ArrowUpRight size={14}/></a>
        <span className="sidebar-foot">Research tools. Not investment advice.</span>
      </div>
    </aside>
    {sideOpen&&<button className="sidebar-backdrop" aria-label="Close menu" onClick={()=>setSideOpen(false)}/>}
    <div className="main-shell">
      <header className="topbar"><div className="breadcrumb"><button className="mobile-menu icon-button" aria-label="Open menu" onClick={()=>setSideOpen(true)}><Menu size={20}/></button><span>Workspace</span><ChevronRight size={14}/><strong>{page==="rules"?"Methodology":page==="health"?"Data & automation":"Guru scans"}</strong></div>
        <div className="topbar-right"><span className="eod-tag"><span className="tiny-dot"/>EOD DATA</span><a href={REPO} target="_blank" rel="noreferrer" className="icon-button" aria-label="Open GitHub repository"><GitBranch size={17}/></a><button className="icon-button" aria-label={`Switch to ${dark?"light":"dark"} mode`} onClick={()=>setDark(!dark)}>{dark?<Sun size={18}/>:<Moon size={18}/>}</button><span className="avatar">AC</span></div></header>
      <main id="main">
        <div className="page-heading"><div><div className="eyebrow">THE INDIAN MOMENTUM DESK</div><h1>{page==="rules"?"Know exactly what qualifies.":page==="health"?"Data you can trace.":scan==="multi"?"Where the gurus agree.":"Different masters. One watchlist."}</h1><p>{page==="scanner"?"Nine public-method scans. Your NSE universe. Find the overlap before the next session.":page==="rules"?"Published criteria, India-specific adaptations and every numerical choice, in the open.":"Independent daily acquisition, dated snapshots and visible coverage checks."}</p></div>
          <div className="heading-actions">{page==="scanner"&&<><button className="button subtle" onClick={()=>setPage("rules")}><Settings2 size={16}/>Scan rules</button><button className="button primary" onClick={exportCSV} disabled={!data}><Download size={16}/>Export CSV</button></>}</div>
        </div>
        {error&&<div role="alert" className="notice danger">{error}<button onClick={()=>load(session)}>Retry</button></div>}
        {data?.market_data.bootstrap&&<div className="notice warning"><Info size={17}/><span>Initial BYOD snapshot from your existing price files. The first independent GitHub refresh has not finished yet. All signals are dated {data.last_trading_date}; missing fundamentals stay unknown.</span></div>}
        {data&&!data.market_data.bootstrap&&feed==="bundled"&&<div className="notice"><Info size={16}/><span>Using the bundled verified snapshot for {data.last_trading_date}; the GitHub feed is unavailable. Refresh to retry.</span></div>}
        {loading&&!data?<div className="loading-grid">{[0,1,2,3].map(i=><div key={i} className="skeleton"/>)}</div>:data&&<>
          <section className="universe-strip" aria-label="Universe filters"><div className="universe-title"><Filter size={15}/><strong>Your universe</strong></div><span>Market cap <b>&gt; ₹500 Cr</b></span><span>ADV20 <b>&gt; 70K</b></span><span>Traded value20 <b>&gt; ₹3 Cr</b></span><span>ADR20 <b>&gt; 3%</b></span><button onClick={()=>setPage("health")}>{data.qualified_count.toLocaleString("en-IN")} eligible<ArrowUpRight size={13}/></button></section>
          {page==="scanner"&&<>
            <section className="metric-strip" aria-label="Scan summary">
              <div><span>ELIGIBLE UNIVERSE</span><strong>{data.qualified_count.toLocaleString("en-IN")}<small>NSE stocks</small></strong><p>Same-session EOD prices</p></div>
              <div><span>ON THE RADAR</span><strong>{matched}<small>unique stocks</small></strong><p>Matched at least one scan</p></div>
              <div className="metric-featured"><span><Layers3 size={13}/>MULTI-SCAN CONFLUENCE</span><strong>{multi}<small>stocks</small></strong><p>Present in {minimum}+ distinct scans</p></div>
              <div><span>MARKET CONTEXT</span><strong className="regime">{data.market_regime}<span className={`regime-dot ${data.market_regime==="Constructive"?"positive":""}`}/></strong><p>Nifty MidSmallcap 400 / SMA50</p></div>
            </section>
            <div className="section-heading"><div><h2>{scan==="all"?"The guru board":scan==="multi"?"Multi-scan overlap":data.scans.find(s=>s.id===scan)?.name}</h2><span>Independent ideas. Shared conviction.</span></div><div className="session-control"><span>SESSION</span><select aria-label="Session date" value={session} onChange={e=>{setSession(e.target.value);load(e.target.value)}}><option value="latest">{data.last_trading_date} · Latest</option>{sessions.filter(s=>s!==data.last_trading_date).map(s=><option key={s}>{s}</option>)}</select><button className="icon-button" aria-label="Refresh published snapshot" onClick={()=>load(session,true)}><RefreshCw size={15} className={refreshing?"spin":""}/></button></div></div>
            <div className="toolbar"><div className="search-field"><Search size={16}/><input aria-label="Search symbols or companies" placeholder="Search symbol or company..." value={search} onChange={e=>setSearch(e.target.value)}/>{search&&<button aria-label="Clear search" className="icon-button" onClick={()=>setSearch("")}><X size={14}/></button>}</div>
              <label className={`filter-toggle ${onlyMulti?"enabled":""}`}><input type="checkbox" checked={onlyMulti} onChange={e=>setOnlyMulti(e.target.checked)}/><Layers3 size={15}/>Multi-scan only</label>
              <select className="select-small" aria-label="Minimum overlap" value={minimum} onChange={e=>setMinimum(+e.target.value)}>{[2,3,4,5].map(n=><option key={n} value={n}>{n}+ scans</option>)}</select>
              <div className="toolbar-spacer"/>
              <select aria-label="EP gap mode" className="select-small" value={original?"original":"india"} onChange={e=>setOriginal(e.target.value==="original")}><option value="india">EP: India &gt;3% gap</option><option value="original">EP: Original ≥10% gap</option></select>
              <select aria-label="Sort stocks" className="select-small" value={sort} onChange={e=>setSort(e.target.value)}><option value="matches">Sort: Scan count</option><option value="change">Sort: Daily move</option><option value="rvol">Sort: RVOL</option><option value="rs">Sort: RS 3M</option><option value="symbol">Sort: Symbol</option></select>
              <div className="view-switch"><button aria-label="Board view" aria-pressed={view==="board"} className={view==="board"?"selected":""} onClick={()=>setView("board")}><Grid2X2 size={16}/></button><button aria-label="Matrix view" aria-pressed={view==="matrix"} className={view==="matrix"?"selected":""} onClick={()=>setView("matrix")}><Table2 size={17}/></button></div>
            </div>
            {view==="board"?<div className="board-wrapper"><div className="board-scroll" id="guru-board">
              {(scan==="all"||scan==="multi")&&<ScanColumn id="multi" name="Multi-scan overlap" sub={`${minimum}+ scans · strongest confluence`} featured rows={rows.filter(r=>activeScans(r,original).length>=minimum)} copy={copy} copied={copied} select={setSelected} original={original} onRules={()=>setMessage("Overlap counts distinct scan IDs, not repeated appearances inside one scan. Related scans are not statistically independent.")}/>}
              {scan!=="multi"&&visibleScans.map(s=><ScanColumn key={s.id} id={s.id} name={s.name} sub={s.kind} rows={rows.filter(r=>activeScans(r,original).includes(s.id))} copy={copy} copied={copied} select={setSelected} original={original} onRules={()=>chooseRule(s.id)}/>)}
            </div><div className="board-footer"><span><Info size={13}/>Select a stock to inspect every scan gate. EP lists contain unverified technical candidates.</span><div><button className="icon-button" aria-label="Scroll board left" onClick={()=>document.getElementById("guru-board")?.scrollBy({left:-500,behavior:"smooth"})}><ChevronLeft size={17}/></button><span>EXPLORE ALL SCANS</span><button className="icon-button" aria-label="Scroll board right" onClick={()=>document.getElementById("guru-board")?.scrollBy({left:500,behavior:"smooth"})}><ChevronRight size={17}/></button></div></div></div>:
            <section className="matrix-panel"><div className="matrix-actions"><span>{matrixRows.length} stocks <small>· a mark means a scan match, not a buy signal</small></span><label><input type="checkbox" checked={showAll} onChange={e=>setShowAll(e.target.checked)}/> Include unmatched</label><button className="button subtle" onClick={()=>copy(matrixRows,"matrix")}><Clipboard size={14}/>Copy all symbols</button></div><div className="table-scroll"><table><thead><tr><th>Stock</th><th><button onClick={()=>setSort("matches")}>Scans<ArrowDown size={12}/></button></th><th>Price</th><th><button onClick={()=>setSort("change")}>Day %<ArrowDownUp size={12}/></button></th><th><button onClick={()=>setSort("rvol")}>RVOL<ArrowDownUp size={12}/></button></th>{data.scans.map(s=><th key={s.id} title={s.name}><button onClick={()=>chooseRule(s.id)}>{abbreviations[s.id]}</button></th>)}<th>Kell</th><th>RS 3M</th></tr></thead><tbody>{matrixRows.map(r=><tr key={r.symbol} onClick={()=>setSelected(r)}><td><button className="symbol-button" onClick={()=>setSelected(r)}>{r.symbol}</button><small>{r.name===r.symbol?"NSE":r.name}</small></td><td><span className={`match-count ${activeScans(r,original).length>=minimum?"hot":""}`}>{activeScans(r,original).length}</span></td><td className="mono">₹{money(r.close)}</td><td className={`mono ${r.change_pct>=0?"up":"down"}`}>{signed(r.change_pct)}</td><td className="mono">{num(r.rvol)}×</td>{data.scans.map(s=><td key={s.id} className="match-cell">{activeScans(r,original).includes(s.id)?<Check size={15} aria-label="Match"/>:s.id==="canslim"&&r.gates.canslim.some(g=>g.passed===null)?<span title="Some fundamental inputs unknown">?</span>:<span className="no-match">·</span>}</td>)}<td><span className="phase-badge">{r.phase}</span></td><td className="mono">{num(r.rs_3m,0)}</td></tr>)}</tbody></table>{!matrixRows.length&&<div className="empty-state"><Search size={26}/><strong>No stocks match these filters</strong><p>Try a different symbol, clear the overlap filter, or include unmatched stocks.</p><button className="button" onClick={()=>{setSearch("");setOnlyMulti(false);setScan("all")}}>Reset filters</button></div>}</div></section>}
            <div className="source-line"><span><ShieldCheck size={13}/>Verified session: {data.last_trading_date} · {feed==="github"?"Live repository feed":"Bundled snapshot"} · Refreshed {new Date(data.generated_at).toLocaleString("en-IN",{timeZone:"Asia/Kolkata",day:"2-digit",month:"short",hour:"2-digit",minute:"2-digit"})} IST</span><a href={`${REPO}/actions`} target="_blank" rel="noreferrer">View update log<ArrowUpRight size={12}/></a></div>
          </>}
          {page==="rules"&&<div className="methodology-layout"><nav className="rules-nav" aria-label="Scan rule selection">{data.scans.map(s=><button key={s.id} className={ruleScan===s.id?"selected":""} onClick={()=>setRuleScan(s.id)}>{s.name}<ChevronRight size={14}/></button>)}</nav><article className="rules-card"><div className="eyebrow">{selectedRule?.guru}</div><h2>{selectedRule?.name}</h2><span className="method-badge">{selectedRule?.kind}</span><p>{selectedRule?.description}</p><h3>What qualifies</h3><ol className="rule-list">{selectedRule?.rules.map((r,i)=><li key={i}>{r}</li>)}</ol><h3>Read the public methodology</h3><div className="source-links">{selectedRule?.sources.map(s=><a key={s.url} href={s.url} target="_blank" rel="noreferrer">{s.title}<ExternalLink size={14}/></a>)}</div><div className="rules-note"><Info size={18}/><p>These scans are discovery tools, not entry instructions. Price structures, catalysts, corporate actions, circuits and trade liquidity still need chart-level review. Two related scan matches do not imply two independent edges.</p></div><button className="button primary" onClick={()=>navigate(ruleScan)}>View matching stocks<ArrowRight size={16}/></button></article></div>}
          {page==="health"&&<div className="health-layout"><article className="rules-card"><div className="eyebrow">DAILY PIPELINE</div><h2>19:30 IST. Every day.</h2><p>The GitHub Actions workflow independently acquires the NSE EQ listing, EOD prices, current shares outstanding and the benchmark. It validates the session before publishing. GitHub schedules are best-effort, not an exact-time guarantee.</p><div className="pipeline-flow"><span>Acquire</span><ArrowRight size={16}/><span>Validate</span><ArrowRight size={16}/><span>Scan</span><ArrowRight size={16}/><span>Publish</span></div><dl className="health-values"><div><dt>Schedule (UTC)</dt><dd>0 14 * * *</dd></div><div><dt>Latest completed session</dt><dd>{data.last_trading_date}</dd></div><div><dt>Benchmark</dt><dd>{data.benchmark}</dd></div><div><dt>Market context proxy</dt><dd>{data.market_regime}</dd></div><div><dt>Official EQ listings</dt><dd>{data.market_data.official_listing_count??"Unknown"}</dd></div><div><dt>Listing price coverage</dt><dd>{num(data.market_data.listing_history_coverage_pct,2)}%</dd></div><div><dt>Same-session coverage</dt><dd>{num(data.market_data.same_session_coverage_pct,2)}%</dd></div><div><dt>Shares coverage</dt><dd>{num(data.market_data.shares_coverage_pct,2)}%</dd></div><div><dt>Stocks with ≥100 bars</dt><dd>{data.qualified_count}</dd></div><div><dt>CAN SLIM fundamental candidates checked</dt><dd>{data.market_data.fundamental_candidates??"Unknown"}</dd></div><div><dt>Fundamentals available</dt><dd>{data.market_data.fundamentals_available??"Unknown"}</dd></div><div><dt>Source mode</dt><dd>{data.market_data.mode}</dd></div></dl><a className="button primary" href={`${REPO}/actions/workflows/daily-update.yml`} target="_blank" rel="noreferrer">Open workflow & run manually<ExternalLink size={15}/></a></article><article className="rules-card"><h2>Definitions & safeguards</h2><ul className="rule-list">{data.notes.map((n,i)=><li key={i}>{n}</li>)}</ul><h3>Data provenance</h3><p>NSE EQ listing and index-close archives; Yahoo Finance EOD history, shares and financial statements via yfinance. The page shows one completed session, never a mix of current and stale stocks. A failed validation leaves the last good snapshot untouched.</p><p>The code and automated workflow are public. This dashboard has no brokerage connection, order placement, account credentials or portfolio information.</p><h3>Coverage limitations</h3><p>Insufficient history, missing shares or incomplete fundamentals can exclude a stock or leave a check unknown. A zero-match column can be a legitimate scan result. EP catalysts are unverified unless separately researched.</p></article></div>}
        </>}
        <footer><span>{svgLogo}<b>guruscreen</b><span>Public methods. Indian markets.</span></span><a href="https://x.com/SteveDJacobs/status/2109436930198773904" target="_blank" rel="noreferrer">Inspired by Steve Jacobs' Guru Scans<ArrowUpRight size={12}/></a></footer>
      </main>
    </div>
    <div className="toast-region" role="status" aria-live="polite">{message&&<div className="toast"><CheckCheck size={17}/>{message}<button className="icon-button" aria-label="Dismiss message" onClick={()=>setMessage("")}><X size={15}/></button></div>}<textarea id="copy-fallback" hidden aria-label="Symbols to copy manually" onBlur={e=>e.target.hidden=true}/></div>
    {selected&&<div className="modal-backdrop" onMouseDown={e=>{if(e.target===e.currentTarget)setSelected(null)}}><section className="stock-modal" role="dialog" aria-modal="true" aria-labelledby="stock-title"><header><div><div className="eyebrow">NSE · {selected.date}</div><h2 id="stock-title">{selected.symbol}<a href={`https://www.tradingview.com/chart/?symbol=${encodeURIComponent("NSE:"+selected.symbol)}`} target="_blank" rel="noreferrer" aria-label="Open stock in TradingView"><ArrowUpRight size={20}/></a></h2><p>{selected.name}</p></div><button autoFocus className="icon-button" aria-label="Close stock details" onClick={()=>setSelected(null)}><X size={20}/></button></header><div className="stock-summary"><strong>₹{money(selected.close)}<span className={selected.change_pct>=0?"up":"down"}>{signed(selected.change_pct)}</span></strong><span className="confluence-label">{selectedMatches.length} scan{selectedMatches.length!==1?"s":""}<Layers3 size={16}/></span></div><div className="stock-metrics"><div><span>RVOL20</span><strong>{num(selected.rvol)}×</strong></div><div><span>OPEN GAP</span><strong>{signed(selected.gap_pct)}</strong></div><div><span>RS 3M</span><strong>{num(selected.rs_3m,0)}</strong></div><div><span>KELL PHASE</span><strong>{selected.phase}</strong></div><div><span>ATR / SMA50</span><strong>{num(selected.atr_extension)}×</strong></div><div><span>CAP (CR)</span><strong>₹{money(selected.market_cap_cr)}</strong></div></div>
      <div className="chart-header"><span>DAILY PRICE · LAST 100 SESSIONS</span><div><i/>Close <i className="ema10"/>EMA10 <i className="ema20"/>EMA20</div></div><div className="price-chart">{chartLoading?<div className="chart-placeholder">Loading dated chart…</div>:chartError?<div className="chart-placeholder">{chartError}</div>:<ResponsiveContainer width="100%" height={230}><ComposedChart data={bars} margin={{top:10,right:5,bottom:0,left:5}}><CartesianGrid stroke="var(--border)" vertical={false}/><XAxis dataKey="t" tickFormatter={v=>v.slice(5)} minTickGap={45} tick={{fontSize:11,fill:"var(--muted)"}} axisLine={false} tickLine={false}/><YAxis domain={["auto","auto"]} width={55} tick={{fontSize:11,fill:"var(--muted)"}} axisLine={false} tickLine={false}/><Tooltip contentStyle={{background:"var(--surface)",borderColor:"var(--border)",color:"var(--text)"}} labelStyle={{color:"var(--text)"}}/><Line name="Close" dataKey="c" stroke="var(--accent)" strokeWidth={2} dot={false} isAnimationActive={false}/><Line name="EMA10" dataKey="e10" stroke="#a07929" dot={false} strokeWidth={1} isAnimationActive={false}/><Line name="EMA20" dataKey="e20" stroke="#668aa3" dot={false} strokeWidth={1} isAnimationActive={false}/></ComposedChart></ResponsiveContainer>}</div>
      <div className="catalyst-note"><Info size={17}/><div><strong>Catalyst: {selected.catalyst}</strong><p>Price and volume cannot establish the news behind an EP. Verify exchange announcements and earnings before treating it as an episodic pivot.</p></div></div>
      <h3 className="gate-heading">Every scan, explained</h3><div className="stock-gates">{data?.scans.map(s=><details key={s.id} open={selectedMatches.includes(s.id)}><summary><span className={`gate-state ${selectedMatches.includes(s.id)?"passed":""}`}>{selectedMatches.includes(s.id)?<Check size={14}/>:s.id==="canslim"&&selected.gates.canslim.some(g=>g.passed===null)?"?":"·"}</span><strong>{s.name}</strong><span>{selectedMatches.includes(s.id)?"Match":s.id==="canslim"&&selected.gates.canslim.some(g=>g.passed===null)?"Missing inputs":"Not matched"}</span></summary><ul>{(selected.gates[s.id==="q_ep"&&original?"q_ep_original":s.id]||[]).map((g,i)=><li key={i}><span className={`gate-status ${g.passed===true?"yes":g.passed===false?"no":"unknown"}`}>{g.passed===null?"?":g.passed?"✓":"×"}</span><span>{g.label}</span><b>{g.value==="None"||g.value==="null"?"Unknown":g.value}</b></li>)}</ul></details>)}</div>
      {selected.warnings.length>0&&<div className="stock-warnings"><h3>Review flags</h3>{selected.warnings.map((w,i)=><p key={i}>{w}</p>)}</div>}<div className="modal-footer"><span>Fundamentals: {selected.fundamentals_status}</span><button className="button primary" onClick={()=>copy([selected],"stock")}><Clipboard size={15}/>Copy symbol</button></div></section></div>}
  </div>
}

function ScanColumn({id,name,sub,featured=false,rows,copy,copied,select,original,onRules}:{id:string;name:string;sub:string;featured?:boolean;rows:Stock[];copy:(r:Stock[],id:string)=>void;copied:string;select:(r:Stock)=>void;original:boolean;onRules:()=>void}){
  const [limit,setLimit]=useState(30);
  useEffect(()=>setLimit(30),[rows.length]);
  return <section className={`scan-column ${featured?"featured":""}`} aria-label={name}>
    <header className="column-heading"><div><span className="column-kicker">{featured?<><Layers3 size={13}/>THE OVERLAP</>:"GURU SCAN"}</span><h3>{name}<span>{rows.length}</span></h3><p>{sub}</p></div><div className="column-actions"><button onClick={()=>copy(rows,id)} aria-label={`Copy all ${name} symbols`} className={`copy-button ${copied===id?"copied":""}`}>{copied===id?<Check size={13}/>:<Clipboard size={13}/>}<span>{copied===id?"Copied":"Copy all"}</span></button><button className="icon-button" aria-label={`${name} rules`} onClick={onRules}><Info size={14}/></button></div></header>
    <div className="column-body">{rows.length?rows.slice(0,limit).map(r=><button className="stock-card" key={r.symbol} onClick={()=>select(r)}><div className="card-top"><strong>{r.symbol}</strong><span className={`day-change ${r.change_pct>=0?"up":"down"}`}>{signed(r.change_pct)}</span></div><div className="card-middle"><span>₹{money(r.close)}</span><span>{num(r.rvol)}× <small>RVOL</small></span></div><div className="card-bottom"><span className="mini-tags">{activeScans(r,original).map(s=><span key={s} title={s}>{abbreviations[s]}</span>)}</span><span className="card-phase" title={r.phase_name}>{r.phase}</span></div>{featured&&<div className="card-confluence"><span>{activeScans(r,original).length} scan matches</span><ArrowUpRight size={13}/></div>}</button>):<div className="column-empty"><ListFilter size={23}/><strong>No qualifying stocks</strong><p>Strict criteria can produce an empty list. View the rules or wait for the next session.</p><button onClick={onRules}>Review criteria<ArrowRight size={13}/></button></div>}{rows.length>limit&&<button className="load-more" onClick={()=>setLimit(limit+40)}>Show {Math.min(40,rows.length-limit)} more ({rows.length-limit} remaining)<ArrowDown size={14}/></button>}</div>
  </section>
}
export default App;
