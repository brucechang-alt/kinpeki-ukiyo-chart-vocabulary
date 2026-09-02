#!/usr/bin/env node
const http = require('http');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { chromium } = require('playwright');

const root = path.resolve(__dirname, '..');
const qaDir = path.join(root, 'qa');
const chromePath = process.env.CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
fs.mkdirSync(qaDir, {recursive: true});
const mime = {'.html':'text/html; charset=utf-8','.css':'text/css; charset=utf-8','.js':'text/javascript; charset=utf-8','.json':'application/json; charset=utf-8','.svg':'image/svg+xml','.png':'image/png','.jpg':'image/jpeg','.md':'text/markdown; charset=utf-8'};

const editions = [
  {locale:'zh', page:'index.html', manifest:'manifest.json', posterSource:'kinpeki-ukiyo-chart-vocabulary.html', poster:'kinpeki-ukiyo-poster.png', preview:'kinpeki-ukiyo-preview.jpg', mobile:'mobile-390.png', grayscale:'kinpeki-ukiyo-poster-grayscale.png', svgRoot:''},
  {locale:'en', page:'index-en.html', manifest:'manifest-en.json', posterSource:'kinpeki-ukiyo-chart-vocabulary-en.html', poster:'kinpeki-ukiyo-poster-en.png', preview:'kinpeki-ukiyo-preview-en.jpg', mobile:'mobile-390-en.png', grayscale:'kinpeki-ukiyo-poster-en-grayscale.png', svgRoot:'en'},
  {locale:'ja', page:'index-ja.html', manifest:'manifest-ja.json', posterSource:'kinpeki-ukiyo-chart-vocabulary-ja.html', poster:'kinpeki-ukiyo-poster-ja.png', preview:'kinpeki-ukiyo-preview-ja.jpg', mobile:'mobile-390-ja.png', grayscale:'kinpeki-ukiyo-poster-ja-grayscale.png', svgRoot:'ja'}
];

function walk(dir) {
  return fs.readdirSync(dir,{withFileTypes:true}).flatMap(e=>e.isDirectory()?walk(path.join(dir,e.name)):[path.join(dir,e.name)]);
}
function startServer(){
  return new Promise(resolve=>{
    const server=http.createServer((req,res)=>{
      const clean=decodeURIComponent(req.url.split('?')[0]);
      if(clean==='/favicon.ico'){res.writeHead(204);res.end();return;}
      const candidate=path.resolve(root,'.'+(clean==='/'?'/index.html':clean));
      if(!candidate.startsWith(root+path.sep)||!fs.existsSync(candidate)||fs.statSync(candidate).isDirectory()){res.writeHead(404);res.end('Not found');return;}
      res.writeHead(200,{'content-type':mime[path.extname(candidate).toLowerCase()]||'application/octet-stream'});fs.createReadStream(candidate).pipe(res);
    });
    server.listen(0,'127.0.0.1',()=>resolve(server));
  });
}
function luminance(hex){
  const rgb=hex.match(/[0-9a-f]{2}/gi).map(x=>parseInt(x,16)/255).map(v=>v<=.04045?v/12.92:Math.pow((v+.055)/1.055,2.4));
  return .2126*rgb[0]+.7152*rgb[1]+.0722*rgb[2];
}
function contrast(a,b){const [hi,lo]=[luminance(a),luminance(b)].sort((x,y)=>y-x);return Number(((hi+.05)/(lo+.05)).toFixed(2));}
function sha256(file){return crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');}
function cjkVisibleText(body){
  return [...body.matchAll(/<(?:title|desc|text)\b[^>]*>([\s\S]*?)<\/(?:title|desc|text)>/gi)].map(m=>m[1].replace(/<[^>]+>/g,'')).join(' ');
}

(async()=>{
  const failures=[];
  const svgAudit={};
  const oldColours=['#006f91','#2f8456','#b97a12','#c44530','#f3e6c6','#28231b','#704c99','#f3e7cf','#1e1b17','#194d78','#c84a3a','#4e7256','#b97832','#755a78','#c9a64a'];

  for(const edition of editions){
    const chartRoot=path.join(root,'charts',edition.svgRoot);
    const svgFiles=walk(chartRoot).filter(f=>f.endsWith('.svg')&&(edition.svgRoot||(!f.includes(`${path.sep}en${path.sep}`)&&!f.includes(`${path.sep}ja${path.sep}`))));
    const audit={count:svgFiles.length,missingStyle:[],oldColors:[],gradients:[],missingTitle:[],missingDesc:[],englishCjk:[]};
    if(svgFiles.length!==67) failures.push(`${edition.locale}: expected 67 SVGs, found ${svgFiles.length}`);
    for(const file of svgFiles){
      const raw=fs.readFileSync(file,'utf8');
      const body=raw.toLowerCase();
      const relative=path.relative(root,file);
      if(!body.includes('data-style="kinpeki-ukiyo"'))audit.missingStyle.push(relative);
      if(oldColours.some(c=>body.includes(c)))audit.oldColors.push(relative);
      if(/lineargradient|radialgradient/.test(body))audit.gradients.push(relative);
      if(!body.includes('<title'))audit.missingTitle.push(relative);
      if(!body.includes('<desc'))audit.missingDesc.push(relative);
      if(edition.locale==='en'&&/[\u3400-\u9fff]/u.test(cjkVisibleText(raw))) audit.englishCjk.push(relative);
    }
    svgAudit[edition.locale]=audit;
    if(audit.missingStyle.length||audit.oldColors.length||audit.gradients.length||audit.missingTitle.length||audit.missingDesc.length||audit.englishCjk.length)failures.push(`${edition.locale}: SVG contract failure`);
  }

  const manifestAudit={};
  for(const edition of editions){
    const manifest=JSON.parse(fs.readFileSync(path.join(root,'charts',edition.manifest),'utf8'));
    const charts=manifest.families.flatMap(f=>f.charts);
    const missingFiles=charts.filter(c=>!fs.existsSync(path.join(root,c.file))).map(c=>c.file);
    manifestAudit[edition.locale]={version:manifest.version,families:manifest.families.length,charts:charts.length,missingFiles};
    if(manifest.version!=='1.0.0'||manifest.families.length!==9||charts.length!==67||missingFiles.length)failures.push(`${edition.locale}: manifest contract failure`);
  }

  const localeAudit={};
  for(const edition of editions){
    const locale=JSON.parse(fs.readFileSync(path.join(root,'locales',`${edition.locale}.json`),'utf8'));
    localeAudit[edition.locale]={language:locale.lang||edition.locale,keys:Object.keys(locale).length};
  }

  const artFile=path.join(root,'assets','hokusai-great-wave-reference.jpg');
  const artAudit={file:path.relative(root,artFile),bytes:fs.statSync(artFile).size,sha256:sha256(artFile),expectedWidth:2000,expectedHeight:1350};
  if(artAudit.bytes>800*1024) failures.push(`art reference exceeds 800KB: ${artAudit.bytes}`);

  const contrastAudit={inkOnPaper:contrast('181a1b','fbf3de'),prussianBlueTextOnPaper:contrast('004b7a','fbf3de'),vermilionMarkOnPaper:contrast('e24832','fbf3de'),vermilionTextOnPaper:contrast('b83326','fbf3de'),greenTextOnPaper:contrast('2f6d49','fbf3de'),yellowTextOnPaper:contrast('905d0b','fbf3de'),purpleTextOnPaper:contrast('713c73','fbf3de'),goldTextOnPaper:contrast('81620b','fbf3de'),paperOnInk:contrast('fbf3de','181a1b')};
  if(contrastAudit.inkOnPaper<7||contrastAudit.prussianBlueTextOnPaper<4.5||contrastAudit.vermilionMarkOnPaper<3||contrastAudit.vermilionTextOnPaper<4.5||contrastAudit.greenTextOnPaper<4.5||contrastAudit.yellowTextOnPaper<4.5||contrastAudit.purpleTextOnPaper<4.5||contrastAudit.goldTextOnPaper<4.5)failures.push('key contrast below target');

  const server=await startServer();
  const port=server.address().port;
  const browser=await chromium.launch({headless:true,executablePath:chromePath});
  const browserFailures=[];
  const languages={};

  for(const edition of editions){
    const manifest=JSON.parse(fs.readFileSync(path.join(root,'charts',edition.manifest),'utf8'));
    const page=await browser.newPage({viewport:{width:1440,height:1000},deviceScaleFactor:1});
    page.on('console',m=>{if(m.type()==='error')browserFailures.push(`${edition.locale}:console:${m.text()}`)});
    page.on('requestfailed',r=>browserFailures.push(`${edition.locale}:request:${r.url()}`));
    await page.goto(`http://127.0.0.1:${port}/${edition.page}`,{waitUntil:'networkidle'});
    await page.waitForFunction(()=>document.querySelectorAll('.chart-card').length===67);
    await page.waitForTimeout(500);
    const desktop=await page.evaluate(()=>{
      const art=document.querySelector('.art-reference img');
      return {cards:document.querySelectorAll('.chart-card').length,filters:document.querySelectorAll('#filters button').length,downloads:document.querySelectorAll('.chart-card a[download]').length,width:document.documentElement.scrollWidth,viewport:document.documentElement.clientWidth,broken:[...document.images].filter(i=>!i.complete||i.naturalWidth===0).length,title:document.title,art:{width:art.naturalWidth,height:art.naturalHeight}};
    });
    const filterAudit=await page.evaluate(()=>{
      const rows=[];const buttons=[...document.querySelectorAll('#filters button')];
      for(const button of buttons){button.click();rows.push({label:button.textContent.trim(),cards:document.querySelectorAll('.chart-card').length});}
      buttons[0].click();return rows;
    });
    await page.screenshot({path:path.join(root,'assets',edition.preview),type:'jpeg',quality:91});

    const poster=await browser.newPage({viewport:{width:2400,height:1200},deviceScaleFactor:1});
    poster.on('requestfailed',r=>browserFailures.push(`${edition.locale}:poster:${r.url()}`));
    await poster.goto(`http://127.0.0.1:${port}/src/${edition.posterSource}`,{waitUntil:'networkidle'});
    await poster.waitForFunction(()=>document.querySelectorAll('.family-panel').length===9&&document.querySelectorAll('.chart-shell img').length===67);
    await poster.waitForTimeout(600);
    const posterMetrics=await poster.evaluate(()=>{
      const art=document.querySelector('.poster-art-image img');
      return {width:document.documentElement.scrollWidth,height:document.documentElement.scrollHeight,families:document.querySelectorAll('.family-panel').length,charts:document.querySelectorAll('.chart-shell img').length,broken:[...document.images].filter(i=>!i.complete||i.naturalWidth===0).length,art:{width:art.naturalWidth,height:art.naturalHeight}};
    });
    await poster.screenshot({path:path.join(root,'assets',edition.poster),fullPage:true});
    await poster.evaluate(()=>document.documentElement.style.filter='grayscale(1)');
    await poster.screenshot({path:path.join(qaDir,edition.grayscale),fullPage:true});

    const mobile=await browser.newPage({viewport:{width:390,height:844},deviceScaleFactor:1});
    mobile.on('requestfailed',r=>browserFailures.push(`${edition.locale}:mobile:${r.url()}`));
    await mobile.goto(`http://127.0.0.1:${port}/${edition.page}`,{waitUntil:'networkidle'});
    await mobile.waitForFunction(()=>document.querySelectorAll('.chart-card').length===67);
    await mobile.waitForTimeout(400);
    const mobileMetrics=await mobile.evaluate(()=>({width:document.documentElement.scrollWidth,viewport:document.documentElement.clientWidth,cards:document.querySelectorAll('.chart-card').length,broken:[...document.images].filter(i=>!i.complete||i.naturalWidth===0).length,firstCardHeight:Math.round(document.querySelector('.chart-card').getBoundingClientRect().height),languageLinks:document.querySelectorAll('.lang-switch a').length}));
    await mobile.screenshot({path:path.join(qaDir,edition.mobile),fullPage:false});

    await page.close();await poster.close();await mobile.close();
    const filterExpected=[67,...manifest.families.map(f=>f.charts.length)];
    if(filterAudit.some((row,index)=>row.cards!==filterExpected[index]))failures.push(`${edition.locale}: filter count mismatch`);
    if(desktop.cards!==67||desktop.filters!==10||desktop.downloads!==67||posterMetrics.families!==9||posterMetrics.charts!==67)failures.push(`${edition.locale}: browser count mismatch`);
    if(desktop.width>desktop.viewport||mobileMetrics.width>mobileMetrics.viewport)failures.push(`${edition.locale}: horizontal overflow`);
    if(desktop.broken||posterMetrics.broken||mobileMetrics.broken)failures.push(`${edition.locale}: broken images`);
    if(desktop.art.width!==2000||desktop.art.height!==1350||posterMetrics.art.width!==2000||posterMetrics.art.height!==1350)failures.push(`${edition.locale}: art source dimensions changed`);
    if(posterMetrics.width!==2400)failures.push(`${edition.locale}: poster width ${posterMetrics.width}, expected 2400`);
    if(mobileMetrics.languageLinks!==3)failures.push(`${edition.locale}: mobile language switch missing`);
    languages[edition.locale]={desktop,filterAudit,poster:posterMetrics,mobile:mobileMetrics};
  }

  await browser.close();server.close();
  failures.push(...browserFailures);
  const result={status:failures.length?'FAIL':'PASS',version:'1.0.0',generatedAt:new Date().toISOString(),manifests:manifestAudit,locales:localeAudit,svgAudit,artwork:artAudit,contrastAudit,languages,failures};
  fs.writeFileSync(path.join(root,'validation.json'),JSON.stringify(result,null,2)+'\n');
  console.log(JSON.stringify(result,null,2));
  if(failures.length)process.exit(1);
})().catch(err=>{console.error(err);process.exit(1)});
