'use strict';
// Public-CLI acceptance subset. Does not replace the retained legacy/electrical/native checks.
const {test}=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),cp=require('node:child_process');
const root=path.resolve(__dirname,'..'),binary=process.env.COPPER_TEST_BIN||'copper';
function compile(source){
 const build=path.join(root,'build');fs.mkdirSync(build,{recursive:true});
 const dir=fs.mkdtempSync(path.join(build,'cli-test-')),out=path.join(dir,'board.json');
 try{const p=cp.spawnSync(binary,['compile',source,'--locked','--offline','-o',out],{cwd:root,encoding:'utf8',timeout:60000,windowsHide:true});
  assert.ifError(p.error);assert.equal(p.status,0,p.stdout+p.stderr);
  const b=JSON.parse(fs.readFileSync(out,'utf8'));assert.equal(b.schema,'copperscript-ir/v0.1');return b;
 }finally{if(!path.resolve(dir).startsWith(path.resolve(build)+path.sep))throw Error('Unsafe test cleanup');fs.rmSync(dir,{recursive:true,force:true});}
}
const nets=b=>Object.fromEntries(b.nets.map(n=>[n.name,new Set(n.endpoints)]));
test('modem and logic supplies stay distinct with all source-selected macros',()=>{
 const b=compile('board.copper'),n=nets(b);
 for(const pin of ['U_MODEM.VBAT_1','U_MODEM.VBAT_2','U_MODEM.VBAT_3']){assert.ok(n.V3V8.has(pin));assert.ok(!n.V3V3.has(pin));}
 assert.ok(n.V3V3.has('U_MCU.VDD'));assert.ok(n.V3V3.has('U_NRF.VDD_1'));
 assert.deepEqual(new Set(b.physical_macros.map(m=>m.name)),new Set(['nordic-antenna','logic-buck-boost','modem-buck-boost']));
});
