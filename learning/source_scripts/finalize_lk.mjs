// Assigns shared PBR textures to the placeholder materials exported from Blender and writes final GLBs.
// usage: node finalize.mjs single <outdir> id...   |   node finalize.mjs kit <out.glb> id...
import { NodeIO, Document } from '@gltf-transform/core';
import { ALL_EXTENSIONS, KHRMaterialsEmissiveStrength } from '@gltf-transform/extensions';
import { dedup, prune, unpartition, mergeDocuments } from '@gltf-transform/functions';
import fs from 'fs'; import path from 'path';
const TEX='/workspace/yard/tex', RAW=process.env.KIT_RAW||'/workspace/workkit/raw';
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS);
const tiled=n=>({base:`${n}_c.jpg`,normal:`${n}_n.jpg`,orm:`${n}_orm.jpg`});
const W='/workspace/workkit/tex/'; const wtiled=n=>({base:`${W}${n}_c.jpg`,normal:`${W}${n}_n.jpg`,orm:`${W}${n}_orm.jpg`});
const SPEC={
 ground:tiled('ground'),walk:tiled('walk'),concrete:tiled('concrete'),plaster_old:tiled('plaster_old'),plaster_paint:tiled('plaster_paint'),
 wood:tiled('wood'),paint_wood:tiled('paint_wood'),metal_paint:tiled('metal_paint'),zinc_rusty:{...tiled('zinc_rusty'),double:true},
 atlas_fabric:{base:'yard_atlas.jpg',normal:'yard_atlas_n.jpg',rough:0.92,metal:0,double:true},
 decal:{base:'yard_decals.png',alpha:'BLEND',rough:0.9,metal:0},
 glass:{color:[0.03,0.035,0.04],rough:0.03,metal:0},glass_louvre:{color:[0.14,0.17,0.17],rough:0.08,metal:0},
 plastic:{color:[1,1,1],rough:0.55,metal:0},rubber:{color:[0.035,0.035,0.035],rough:0.92,metal:0},
 metal_dark:{color:[0.12,0.12,0.12],rough:0.55,metal:0.6},steel_galv:{color:[0.55,0.56,0.57],rough:0.45,metal:0.85},
 cable:{color:[0.025,0.025,0.025],rough:0.7,metal:0},water:{color:[0.05,0.07,0.08],rough:0.04,metal:0},
 alu:{color:[0.75,0.75,0.74],rough:0.42,metal:1},charcoal:{color:[0.03,0.03,0.03],rough:0.95,metal:0},
 emit_warm:{color:[1,0.85,0.6],rough:0.4,metal:0,emissive:[1,0.82,0.55],strength:4},
 wood_planks:tiled('wood'),
 emit_cool:{color:[0.92,0.96,1],rough:0.4,metal:0,emissive:[0.9,0.95,1],strength:3},
 tile_floor:wtiled('tile_floor'),terrazzo:wtiled('terrazzo'),worn_tile:wtiled('worn_tile'),hessian:wtiled('hessian'),linen:wtiled('linen'),wood_floor:wtiled('wood_floor'),
 atlas_work:{base:'/workspace/workkit/tex/work_atlas.jpg',rough:0.72,metal:0},
 screen:{base:'/workspace/workkit/tex/work_atlas.jpg',rough:0.25,metal:0,emissive:[1,1,1],strength:1.1,emissiveTex:true},
 mirror:{color:[0.92,0.93,0.94],rough:0.04,metal:1},glass_clear:{color:[0.82,0.9,0.93],rough:0.05,metal:0,alpha:'BLEND',opacity:0.22,double:true},
 chrome:{color:[0.8,0.8,0.8],rough:0.22,metal:1},fabric:{color:[1,1,1],rough:0.95,metal:0},ceramic:{color:[0.9,0.9,0.88],rough:0.3,metal:0},
};
// Poly Haven model materials: read the source gltf, use 512px copies of its maps
const phCache={};
function phSpec(name){
  const [,pid,mname]=name.split('__');
  const dir=`/workspace/workkit/src/phm/${pid}`; const g=JSON.parse(fs.readFileSync(fs.readdirSync(dir).filter(f=>f.endsWith('.gltf')).map(f=>path.join(dir,f))[0]));
  const m=g.materials.find(x=>x.name===mname); if(!m) throw new Error('no ph mat '+name);
  const img=i=>{ if(i==null) return null; const uri=g.images[g.textures[i.index].source].uri; return path.join(dir,uri); };
  const pbr=m.pbrMetallicRoughness||{};
  return {phBase:img(pbr.baseColorTexture),phNormal:img(m.normalTexture),phOrm:img(pbr.metallicRoughnessTexture),phOcc:img(m.occlusionTexture),
          alpha:m.alphaMode,cutoff:m.alphaCutoff,double:m.doubleSided,pid,color:pbr.baseColorFactor?.slice(0,3),rough:pbr.roughnessFactor,metal:pbr.metallicFactor};
}
import { execSync } from 'child_process';
function ph512(src){
  // jpg copies at 512 (PNG kept if it carries alpha)
  const ext=path.extname(src).toLowerCase(); const out=path.join(TEX,'ph',path.basename(src).replace(/_1k/,'_512'));
  if(!fs.existsSync(out)) execSync(`python3 -c "from PIL import Image; im=Image.open('${src}'); im=im.resize((512,512),Image.LANCZOS); im.save('${out}',quality=85,optimize=True)"`);
  return out;
}
const EXTRA={};
Object.assign(SPEC,{hk_marble:wtiled('hk_marble'),hk_porcelain:wtiled('hk_porcelain'),hk_laminate:wtiled('hk_laminate'),hk_bathtile:wtiled('hk_bathtile'),hk_leather:wtiled('hk_leather'),hk_check:{...wtiled('hk_check'),double:true},
 hk_rug:{base:W+'hk_rug_c.jpg',rough:0.95,metal:0},hk_adire:{base:W+'hk_adire_c.jpg',rough:0.85,metal:0},hk_print:{base:W+'hk_print_c.jpg',rough:0.6,metal:0},
 net:{color:[0.97,0.97,0.97],rough:0.9,metal:0,alpha:'BLEND',opacity:0.28,double:true},screen_off:{color:[0.015,0.015,0.02],rough:0.12,metal:0},emit_led:{color:[0.4,0.9,0.5],rough:0.4,metal:0,emissive:[0.3,1,0.4],strength:3}});

Object.assign(SPEC,{lk_board:{color:[0.97,0.97,0.96],rough:0.25,metal:0},lk_slide:{color:[1,1,1],rough:0.35,metal:0,emissive:[0.85,0.85,0.85],strength:1},lk_paper:{color:[0.96,0.95,0.92],rough:0.9,metal:0,double:true}});
async function finalizeDoc(doc){
  const texCache=new Map();
  const T=(file)=>{ const p=path.isAbsolute(file)?file:path.join(TEX,file); if(texCache.has(p)) return texCache.get(p);
    const t=doc.createTexture(path.basename(p)).setImage(fs.readFileSync(p)).setMimeType(p.endsWith('.png')?'image/png':'image/jpeg').setURI(path.basename(p)); texCache.set(p,t); return t; };
  const es=doc.createExtension(KHRMaterialsEmissiveStrength);
  for(const m of doc.getRoot().listMaterials()){
    const name=m.getName(); let s=SPEC[name];
    if(!s && name.startsWith('ph__')) s=phSpec(name);
    if(!s){ console.warn('no spec for material',name); continue; }
    if(EXTRA[name]) s={...s,...EXTRA[name]};
    if(s.base) m.setBaseColorTexture(T(s.base));
    if(s.phBase) m.setBaseColorTexture(T(s.phBase.includes('/tex/ph/')?s.phBase:ph512(s.phBase)));
    if(s.normal) m.setNormalTexture(T(s.normal));
    if(s.phNormal) m.setNormalTexture(T(ph512(s.phNormal)));
    if(s.orm){ const t=T(s.orm); m.setMetallicRoughnessTexture(t); m.setOcclusionTexture(t); m.setRoughnessFactor(1); m.setMetallicFactor(1); }
    if(s.phOrm){ const t=T(ph512(s.phOrm)); m.setMetallicRoughnessTexture(t); m.setRoughnessFactor(s.rough??1); m.setMetallicFactor(s.metal??1); if(s.phOcc) m.setOcclusionTexture(T(ph512(s.phOcc))); }
    if(s.color) m.setBaseColorFactor([...s.color,s.opacity??1]); else m.setBaseColorFactor([1,1,1,1]);
    if(s.rough!=null && !s.orm && !s.phOrm) m.setRoughnessFactor(s.rough);
    if(s.metal!=null && !s.orm && !s.phOrm) m.setMetallicFactor(s.metal);
    m.setAlphaMode(s.alpha||'OPAQUE'); if(s.alpha==='MASK') m.setAlphaCutoff(s.cutoff??0.5);
    m.setDoubleSided(!!s.double);
    if(s.emissive){ m.setEmissiveFactor(s.emissive); if(s.strength) m.setExtension('KHR_materials_emissive_strength',es.createEmissiveStrength().setEmissiveStrength(s.strength)); }
    if(s.emissiveTex){ m.setEmissiveTexture(m.getBaseColorTexture()); }
  }
  // drop TEXCOORD on meshes whose material has no textures? (keep: harmless). Remove unused tangents/attributes.
  await doc.transform(dedup(),prune(),unpartition());
  return doc;
}
const [mode,out,...ids]=process.argv.slice(2);
if(mode==='single'){
  fs.mkdirSync(out,{recursive:true});
  for(const id of ids){ const doc=await io.read(`${RAW}/${id}.glb`); await finalizeDoc(doc); doc.getRoot().listScenes()[0].setName(id); await io.write(path.join(out,`${id}.glb`),doc); console.log('wrote',id,fs.statSync(path.join(out,`${id}.glb`)).size); }
} else if(mode==='kit'){
  const doc=new Document(); const scene=doc.createScene('kit');
  for(const id of ids){ const d=await io.read(`${RAW}/${id}.glb`); mergeDocuments(doc,d); }
  // move every root node of every merged scene into one scene
  for(const sc of doc.getRoot().listScenes()){ if(sc===scene) continue; for(const n of sc.listChildren()){ scene.addChild(n); } sc.dispose(); }
  doc.getRoot().setDefaultScene(scene);
  await finalizeDoc(doc);
  // merge buffers
  const bufs=doc.getRoot().listBuffers(); for(const b of bufs.slice(1)) { for(const a of doc.getRoot().listAccessors()) if(a.getBuffer()===b) a.setBuffer(bufs[0]); b.dispose(); }
  await io.write(out,doc); console.log('wrote kit',out,fs.statSync(out).size);
}
