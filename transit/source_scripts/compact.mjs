// Post-process a kit: drop tangents, shrink textures, quantize + meshopt.
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { quantize, meshopt, textureCompress, dedup, prune } from '@gltf-transform/functions';
import { MeshoptEncoder, MeshoptDecoder } from 'meshoptimizer';
import sharp from 'sharp';
import fs from 'fs';
await MeshoptEncoder.ready; await MeshoptDecoder.ready;
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({'meshopt.encoder':MeshoptEncoder,'meshopt.decoder':MeshoptDecoder});
const [inp,out]=process.argv.slice(2);
const doc=await io.read(inp);
for(const m of doc.getRoot().listMeshes()) for(const p of m.listPrimitives()){ const t=p.getAttribute('TANGENT'); if(t){ p.setAttribute('TANGENT',null); } }
const HERO=/BarberShopChair|CashRegister_01_diff|television_02_diff/;
await doc.transform(
  textureCompress({encoder:sharp,targetFormat:'jpeg',quality:78,resize:[256,256],pattern:/_512\.jpg$/, filter:(t)=>!HERO.test(t.getName()||t.getURI())}),
  textureCompress({encoder:sharp,targetFormat:'jpeg',quality:76,resize:[512,512],pattern:/_(c|n|orm)\.jpg$/}),
  textureCompress({encoder:sharp,targetFormat:'jpeg',quality:80,pattern:/work_atlas/}),
  dedup(),prune(),
  ...(process.env.NOQ?[]:[quantize({quantizePosition:14,quantizeNormal:10,quantizeTexcoord:12})]),
  ...(process.env.NOM?[]:[meshopt({encoder:MeshoptEncoder,level:'medium'})]),
);
await io.write(out,doc); console.log('compact',out,fs.statSync(out).size);
