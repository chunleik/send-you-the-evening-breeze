"""Browser QA. Run with a local HTTP server serving ../dist on port 4173."""
from playwright.sync_api import sync_playwright
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'qa-output'; OUT.mkdir(exist_ok=True)
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 errors=[]
 ctx=browser.new_context(viewport={'width':1440,'height':1000},reduced_motion='reduce')
 page=ctx.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://127.0.0.1:4173');page.screenshot(path=str(OUT/'desktop-title.png'))
 assert page.title().startswith('把晚风寄给你')
 page.click('#startBtn');page.wait_for_timeout(1000);page.screenshot(path=str(OUT/'desktop-town.png'))
 page.click('#soundBtn');assert page.locator('#soundBtn').get_attribute('aria-pressed')=='true'
 page.click('#soundBtn')
 choices=['我其实不是回来帮忙的……','也许我也能有另一个第一天','想念不是给别人添麻烦','今天有一点想你，也有一点开心','薄荷：给经过的人泡一杯茶','明天的自己']
 seen=[]
 for target in ['post','bakery','river','garden','post']:
  page.locator('[data-place="'+target+'"]').click()
  page.wait_for_function("!document.querySelector('#dialogue').hidden",timeout=15000)
  for _ in range(100):
   if page.locator('#dialogue').is_hidden():break
   buttons=page.locator('#choices button');count=buttons.count()
   if count:
    labels=buttons.all_text_contents();seen.extend(labels)
    text=page.locator('#dialogueText').inner_text()
    desired=next((a for a in choices if a in labels),None)
    if '第一步' in text:desired='小火预热'
    elif '稳定的热' in text:desired='中火烘烤'
    elif '最后一步' in text:desired='关火，等一会儿'
    if desired:buttons.filter(has_text=desired).click()
    else:buttons.first.click()
   else:page.locator('#nextBtn').click()
   page.wait_for_timeout(35)
  else:raise AssertionError('Dialogue never ended at '+target)
  print('Chapter completed',target,page.locator('#objectiveText').inner_text(),flush=True)
 page.wait_for_selector('#ending:not([hidden])');page.screenshot(path=str(OUT/'desktop-ending.png'))
 assert page.locator('#fragmentCount').inner_text()=='3 / 3'
 assert '薄荷' in page.locator('#endingLetter').inner_text()
 data=page.evaluate("JSON.parse(localStorage.getItem('evening-breeze-story-v1'))")
 assert data['finished'] and data['quest']==5 and len(data['fragments'])==3
 page.click('#returnTown');page.click('#journalBtn');assert page.locator('.memory-card.locked').count()==0;page.click('#closeJournal')
 page.reload();assert page.locator('#continueBtn').is_visible();page.click('#continueBtn');assert page.locator('#fragmentCount').inner_text()=='3 / 3'
 page.click('#menuBtn');page.click('#restartBtn');assert page.locator('#restartConfirm').is_visible();page.click('#cancelRestart');page.click('#resumeBtn')
 mobile=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,reduced_motion='reduce')
 mp=mobile.new_page();mp.on('pageerror',lambda e:errors.append(str(e)));mp.goto('http://127.0.0.1:4173');mp.screenshot(path=str(OUT/'mobile-title.png'))
 mp.tap('#startBtn');mp.wait_for_timeout(1000);mp.screenshot(path=str(OUT/'mobile-town.png'))
 assert mp.locator('#touchControls').is_visible()
 assert mp.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
 mp.locator('[data-place="post"]').tap();mp.wait_for_function("!document.querySelector('#dialogue').hidden",timeout=15000)
 mp.screenshot(path=str(OUT/'mobile-dialogue.png'))
 assert mp.locator('#dialogueText').is_visible()
 assert mp.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
 assert not errors,errors
 (OUT/'results.json').write_text(json.dumps({'passed':True,'errors':errors,'save':data,'choice_labels_seen':seen},ensure_ascii=False,indent=2))
 print('PASS: full playthrough, choices, puzzles, ending, save/continue, journal, sound UI, restart confirmation, mobile layout/touch')
 browser.close()
