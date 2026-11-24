// 브이월드에서 임실 대상 지번 14곳의 필지 경계(LP_PA_CBND_BUBUN)와 주변 건물(LT_C_SPBD)을 받아 vworld_parcels.json으로 저장
// 국내 IP에서만 접속됨. 키는 ../.env 의 VWORLD_KEY (.gitignore로 커밋 제외)
import fs from 'fs';
const key=fs.readFileSync(new URL('../.env',import.meta.url),'utf8').match(/VWORLD_KEY=(\S+)/)[1];
const B='전북특별자치도 임실군 ';
const T=[...['982','272','332','182-2','385-2','212','183-3','214'].map(j=>['임실읍 이도리',j]),
 ...['584-2','489-5','498-6'].map(j=>['관촌면 관촌리',j]),...['387-27','351-8','376-2'].map(j=>['오수면 오수리',j])];
const get=async u=>{for(let i=0;i<3;i++){try{const r=await fetch(u+`&key=${key}`);return await r.json()}catch(e){if(i==2)throw e}}};
const gf=(data,extra)=>get(`https://api.vworld.kr/req/data?service=data&request=GetFeature&version=2.0&format=json&crs=EPSG:4326&geometry=true&attribute=true&size=100&data=${data}&${extra}`);
const out=[];
for(const [d,j] of T){
  const s=await get(`https://api.vworld.kr/req/search?service=search&request=search&version=2.0&crs=EPSG:4326&size=1&type=address&category=parcel&format=json&query=${encodeURIComponent(B+d+' '+j)}`);
  const it=s.response.result?.items?.[0]; if(!it){console.log('NOSEARCH',d,j);continue}
  const p=await gf('LP_PA_CBND_BUBUN',`attrFilter=pnu:=:${it.id}`);
  const f=p.response.result?.featureCollection?.features?.[0];
  if(!f){console.log('NOPARCEL',d,j,JSON.stringify(p.response).slice(0,300));continue}
  const pts=f.geometry.coordinates.flat(Infinity); const xs=pts.filter((_,i)=>i%2==0), ys=pts.filter((_,i)=>i%2==1);
  const m=0.0003, box=[Math.min(...xs)-m,Math.min(...ys)-m,Math.max(...xs)+m,Math.max(...ys)+m];
  const b=await gf('LT_C_SPBD',`geomFilter=BOX(${box.join(',')})`);
  const bf=b.response.result?.featureCollection?.features||[];
  if(b.response.status!='OK'&&b.response.status!='NOT_FOUND')console.log('BLD',b.response.status,JSON.stringify(b.response.error||''));
  out.push({dong:d,jibun:j,pnu:it.id,props:f.properties,geom:f.geometry,buildings:bf.map(x=>({props:x.properties,geom:x.geometry}))});
  console.log(d,j,f.properties.jimok||'',f.properties.jibun,'bld',bf.length);
}
fs.writeFileSync(new URL('vworld_parcels.json',import.meta.url),JSON.stringify(out));
console.log('saved',out.length);
