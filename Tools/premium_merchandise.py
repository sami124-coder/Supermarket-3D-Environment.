"""Dense boutique merchandising for the existing SIPO art scene.

Executed in build_supermarket.py's namespace after redesign_art.py.  This module
adds static environment art only.  All reused groceries retain Kenney CC0 source
provenance; label graphics, cabinets, trays and themed sculptures are original.
Fixture tags let the architectural expansion move displays without stretching
normal-sized products.  No runtime or gameplay components are created.
"""
GROUP = 'Premium merchandising'
MERCH_STATS = {'licensedGroceriesAdded': 0, 'originalPackagedProducts': 0,
               'stockedDisplays': 0, 'pastryTrays': 0}
for key, color, rough, metal in [
    ('BerryGlaze','B81154',.2,.05), ('Pistachio','82C553',.28,0),
    ('Chocolate','492415',.3,0), ('Butter','FFC56B',.36,0),
    ('Porcelain','FAEDDD',.16,.05), ('FrostWhite','E1F8FF',.18,.12),
    ('IceDeep','127BCC',.15,.2), ('Raspberry','EF1875',.2,.03),
    ('GrapeJuice','863AC3',.22,.05), ('LimeJuice','A8D437',.25,0),
    ('PeachJuice','FF942F',.22,0), ('LabelInk','213876',.4,0)]:
    M[key] = mat(key, color, rough, metal)

# A low-poly torus is sufficient for product-scale rolled rims, unlike the
# 96-segment architectural light tubes used elsewhere in the source.
def merch_rim(name, loc, radius, tube, material, segments=24):
    verts=[];faces=[]
    for i in range(segments):
        a=i*math.tau/segments
        for j in range(6):
            b=j*math.tau/6
            verts.append(((radius+tube*math.cos(b))*math.cos(a),
                          (radius+tube*math.cos(b))*math.sin(a),tube*math.sin(b)))
    for i in range(segments):
        for j in range(6):
            faces.append((i*6+j,((i+1)%segments)*6+j,
                          ((i+1)%segments)*6+(j+1)%6,i*6+(j+1)%6))
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
    obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj)
    obj.location=loc;finish(obj,name,material)
    for poly in mesh.polygons:poly.use_smooth=True
    return obj

_merch_finish=finish
_MERCH_UNIT=None
_MERCH_ANCHOR=None
_MERCH_PRODUCT=False

def finish(o,name,ma=None):
    o=_merch_finish(o,name,ma)
    if _MERCH_UNIT:
        o['art_unit']=_MERCH_UNIT;o['art_anchor']=list(_MERCH_ANCHOR)
    if _MERCH_PRODUCT:o['preserve_scale']=True
    return o

def merch_unit(name,anchor):
    global _MERCH_UNIT,_MERCH_ANCHOR
    _MERCH_UNIT=name;_MERCH_ANCHOR=anchor

def merch_food(name,loc,size,rotation=0):
    obj=food(name,loc,size,rotation)
    obj['preserve_scale']=True
    if _MERCH_UNIT:
        obj['art_unit']=_MERCH_UNIT;obj['art_anchor']=list(_MERCH_ANCHOR)
    MERCH_STATS['licensedGroceriesAdded']+=1
    return obj

def price_card(label,loc,width=.72):
    cube('Boutique cream price card',loc,(width,.028,.24),M['Porcelain'],.025)
    text(label,(loc[0],loc[1]-.022,loc[2]),.095,M['LabelInk'],extrude=.001)

def tray(x,y,z,w=1.04,d=.65,material='Gold'):
    cube('Rolled edge pastry serving tray',(x,y,z),(w,d,.032),M[material],.022)
    for yy in (y-d/2,y+d/2):rod('Serving tray rolled lip',(x-w/2,yy,z+.035),(x+w/2,yy,z+.035),.018,M[material])
    for xx in (x-w/2,x+w/2):rod('Serving tray rolled lip',(xx,y-d/2,z+.035),(xx,y+d/2,z+.035),.018,M[material])
    MERCH_STATS['pastryTrays']+=1

def packaged_box(x,y,z,color,label,size=.33):
    """Original cereal/confection carton with front label and printed emblem."""
    global _MERCH_PRODUCT
    _MERCH_PRODUCT=True
    cube('Colorful SIPO gift carton',(x,y,z+size*.64),(size*.77,size*.48,size*1.28),M[color],.012)
    cube('Printed carton label',(x,y-size*.246,z+size*.66),(size*.65,.008,size*.58),M['Porcelain'])
    text(label,(x,y-size*.266,z+size*.76),size*.13,M['LabelInk'],extrude=.0005)
    uv('Printed package fruit emblem',(x,y-size*.269,z+size*.53),(size*.135,.006,size*.12),M[color],12,8)
    cube('Carton sealed top fold',(x,y,z+size*1.29),(size*.77,size*.485,.025),M['Porcelain'])
    MERCH_STATS['originalPackagedProducts']+=1
    _MERCH_PRODUCT=False

# Replenish existing ground-floor shelving with additional product rows,
# organization dividers, category cards and warm under-shelf light strips.
# Kept within the existing shelf/collider footprints.
GROUP='Boutique stocked shelving'
existing_backs=[obj for obj in scene.objects if obj.name.startswith('Shelf backing') and obj.location.z<4]
for bay_index,back in enumerate(existing_backs):
    x,yb,zmid=back.location;y=yb-.34;width=back.dimensions.x;base=zmid-1.64
    merch_unit('Stock bay %02d'%bay_index,(x,y,base))
    kinds=['honey','peanutButter','bottleOil','carton','sodaCan','bag','cartonSmall','bottleKetchup']
    if x<-13 and y>8:kinds=['loaf','bread','croissant','cupcake','muffin','donutChocolate','cookieChocolate']
    elif abs(x)<4 and y>10:kinds=['cartonSmall','fish','cheese','carton']
    elif x>4 and y>15:kinds=['sodaBottle','sodaCan','cartonSmall','carton']
    for row in range(4):
        zz=base+.39+row*.72
        cube('Shelf concealed warm light',(x,y+.20,zz+.59),(width-.20,.045,.025),M['WarmLight'])
        for col in range(max(2,int(width/.35)-1)):
            xx=x-width/2+.28+col*.35
            merch_food(kinds[(col//4+row)%len(kinds)],(xx,y+.15,zz),.32)
        for divider in range(1,4):
            xx=x-width/2+divider*width/4
            cube('Shelf merchandising divider',(xx,y-.01,zz+.21),(.025,.68,.40),M['Porcelain'])
        for col in range(4):
            xx=x-width*.37+col*width*.247
            price_card(['FRESH','SIPO','DAILY','JOY'][col],(xx,y-.514,zz-.04),.37)
    MERCH_STATS['stockedDisplays']+=1

# PRODUCE: concentric, sorted mountains of fruit, slatted market bins, botanical
# details and low satellite stands without closing the garden's walkable edge.
GROUP='Garden harvest boutique'
merch_unit(None,None)
produce_center=(-10,1)
for level,(z,radii) in enumerate([(.63,(2.98,2.66,2.34)),(1.19,(2.43,2.11,1.79)),(1.75,(1.71,1.39,1.07))]):
    for rr in radii:
        count=int(math.tau*rr/.27)
        for j in range(count):
            a=j*math.tau/count
            name=['apple','lemon','tomato','pear','grapes','banana','strawberry','broccoli'][int(j/count*8)]
            merch_food(name,(-10+rr*math.cos(a),1+rr*math.sin(a),z),.31,random.uniform(-.35,.35))
    for sector in range(8):
        a=sector*math.tau/8
        r=radii[0]
        rod('Garden basket sector divider',(-10+radii[-1]*math.cos(a),1+radii[-1]*math.sin(a),z+.045),(-10+r*math.cos(a),1+r*math.sin(a),z+.045),.028,M['Wood'])
for index,(x,y,kind,col) in enumerate([(-13,5,'pineapple','Yellow'),(-10,5.3,'watermelon','Green'),(-6.7,4.2,'cabbage','Pistachio')]):
    merch_unit('Garden harvest crate %d'%index,(x,y,0))
    cube('Produce satellite green stand',(x,y,.52),(1.64,1.20,1.04),M['Green'],.08)
    cube('Slatted harvest crate base',(x,y,1.05),(1.72,1.29,.08),M['Oak'])
    for side in (-1,1):
        for zz in (1.12,1.26,1.40):cube('Harvest crate golden wood slat',(x,y+side*.63,zz),(1.72,.055,.095),M['Oak'])
        for xx in (-.77,.77):cube('Harvest crate corner post',(x+xx,y+side*.60,1.25),(.08,.08,.46),M['Wood'])
    for j in range(4):
        for k in range(3):merch_food(kind,(x-.56+j*.38,y-.42+k*.40,1.10),.42)
    for j in range(3):merch_food(kind,(x-.4+j*.38,y-.08,1.4),.36)
    price_card('GARDEN FRESH',(x,y-.70,1.02),1.13)
    coll('Garden stocked harvest crate',(x,y,.78),(1.75,1.35,1.56))
    for k in range(3):
        rod('Fresh herb stem',(x-.50+k*.46,y+.47,1.33),(x-.50+k*.46,y+.47,1.82),.014,M['LeafDark'])
        for h in range(4):
            s=(-1)**h
            uv('Fresh herb leaves',(x-.50+k*.46+s*.08,y+.47,1.48+h*.07),(.11,.048,.035),M['LeafLight'],10,6)
    MERCH_STATS['stockedDisplays']+=1

# BAKERY: layered glass pastry counter, filled gilt trays and a macaron tower.
GROUP='Premium patisserie merchandising'
# Replace the original sparse loose pastries and cakes where the new glass
# vitrine goes; retained source assets are untouched.
for obj in list(scene.objects):
    p=obj.location
    if -20<p.x<-14 and 9.0<p.y<11.0 and (
        (obj.name.startswith('Kenney ') and 1.39<p.z<1.73) or
        obj.name.startswith('Patisserie tier stand')):
        bpy.data.objects.remove(obj,do_unlink=True)
merch_unit('Bakery jewel counter',(-17,10,0))
# Existing counter top is 1.40 m; add an attractive two-tier glass case.
for x in (-19.72,-14.28):
    for y in (8.94,11.04):rod('Bakery display brass upright',(x,y,1.41),(x,y,2.47),.025,M['Gold'])
for z in (1.44,1.98):
    cube('Patisserie floating glass shelf',(-17,10,z),(5.45,2.07,.04),M['Glass'])
    for j in range(5):
        xx=-19.14+j*1.07
        for row in range(2):
            yy=9.42+row*.91
            tray(xx,yy,z+.045,.97,.76)
            for k in range(3):
                for d in range(2):
                    name=['croissant','donutChocolate','cupcake','muffin','cookieChocolate'][(j+row)%5]
                    merch_food(name,(xx-.30+k*.30,yy-.17+d*.33,z+.075),.25)
        price_card(['CROISSANTS','DONUTS','CUPCAKES','MUFFINS','COOKIES'][j],(xx,8.965,z+.02),.84)
    cube('Pastry shelf edge glow',(-17,8.96,z-.055),(5.35,.035,.025),M['WarmLight'])
cube('Bakery showcase top glazing',(-17,10,2.47),(5.48,2.13,.035),M['Glass'])
# Deliberately open front: merchandise remains legible from the camera.
for side in (-1,1):cube('Bakery cabinet side glazing',(-17+side*2.72,10,1.95),(.025,2.08,1.04),M['Glass'])
for x in (-19.55,-14.65):
    cube('Bread display side plinth',(x,12.40,.70),(1.28,1.30,1.4),M['Orange'],.07)
    for zz in (1.42,1.92,2.42):
        tray(x,12.4,zz,1.26,1.2)
        for j in range(4):merch_food('loafBaguette',(x-.40+j*.26,12.4,zz+.05),.86,math.pi/2)
    price_card('BAKED WITH JOY',(x,11.73,1.17),1.13)
    coll('Baguette boutique stand',(x,12.4,1.15),(1.3,1.3,2.3))
# Visible tiny macarons are actual layered meshes, not a painted surface.
x,y=-17,12.3
cyl('Macaron tower rose pedestal',(x,y,.69),.78,1.38,M['BerryGlaze'],40)
cyl('Macaron tower gold countertop',(x,y,1.40),.83,.055,M['Gold'],40)
coll('Macaron boutique pedestal',(x,y,.72),(1.68,1.68,1.44))
for tier in range(5):
    r=.69-tier*.11;z=1.42+tier*.24
    cyl('Macaron tower porcelain tier',(x,y,z),r+.06,.045,M['Porcelain'],32)
    count=max(5,int(r*22))
    for j in range(count):
        a=j*math.tau/count;xx=x+r*.86*math.cos(a);yy=y+r*.86*math.sin(a)
        color=['Raspberry','Pistachio','Butter','GrapeJuice','Ice'][tier]
        for dz in (.06,.17):uv('French macaron almond shell',(xx,yy,z+dz),(.105,.105,.055),M[color],12,8)
        cyl('Macaron cream filling',(xx,yy,z+.115),.098,.035,M['Porcelain'],16)
text('LA PATISSERIE',(-17,12.86,3.7),.30,M['Gold'])
for index,x in enumerate((-19.4,-17,-14.6)):
    merch_unit('Patisserie celebration cake %d'%index,(x,13.4,0))
    cyl('Celebration cake porcelain column',(x,13.4,.60),.57,1.2,M['Porcelain'],32)
    cyl('Celebration cake gilt salver',(x,13.4,1.25),.63,.08,M['Gold'],32)
    merch_food('cakeBirthday',(x,13.4,1.30),.94)
    price_card('CELEBRATE',(x,12.80,1.05),.86)
    coll('Celebration cake boutique',(x,13.4,.95),(1.28,1.28,1.90))
MERCH_STATS['stockedDisplays']+=7

# CANDY: bright gift boxes, filled confectionery jars, ribboned bonbon sculptures
# and a full curved skirt of candy retail packages around the lollipop garden.
GROUP='Candy boutique abundance'
merch_unit('Candy garden merchandising',(-6.5,8.6,0))
for z,r in ((1.27,1.9),(1.61,1.35)):
    if z>1.3:cyl('Candy gift display terrace',(-6.5,8.6,z-.15),r+.10,.3,M['BerryGlaze'],48)
    for j in range(28 if r>1.5 else 19):
        a=j*math.tau/(28 if r>1.5 else 19)
        xx=-6.5+r*math.cos(a);yy=8.6+r*math.sin(a)
        packaged_box(xx,yy,z,['Candy','Teal','Yellow','Purple'][j%4],['POP','JOY','WOW','YUM'][j%4],.27)
for index,(x,y) in enumerate([(-9.25,10.15),(-4.0,10.9)]):
    merch_unit('Candy confection jar stand %d'%index,(x,y,0))
    cyl('Candy jar pedestal',(x,y,.64),.69,1.28,M['Candy'],40)
    cyl('Candy jar gold platter',(x,y,1.32),.73,.10,M['Gold'],40)
    for j in range(3):
        a=j*math.tau/3;xx=x+.32*math.cos(a);yy=y+.32*math.sin(a)
        cyl('Transparent sweet jar',(xx,yy,1.75),.205,.76,M['Glass'],24)
        for zz in range(6):
            for k in range(4):
                a2=k*math.tau/4+zz*.4
                uv('Colorful loose jelly bean',(xx+.11*math.cos(a2),yy+.11*math.sin(a2),1.42+zz*.09),(.066,.045,.045),M[['Candy','Yellow','Teal','Purple'][(k+zz)%4]],10,6)
        cyl('Candy jar scalloped lid',(xx,yy,2.15),.23,.08,M['Gold'],24)
        uv('Candy jar lid jewel',(xx,yy,2.23),(.07,.07,.06),M['Candy'],12,8)
    price_card('SWEET LITTLE JOYS',(x,y-.75,1.0),1.28)
    coll('Confection jar boutique',(x,y,.9),(1.5,1.5,1.8))
    MERCH_STATS['stockedDisplays']+=1
# Oversized wrapped sweets read clearly against the darker back wall.
merch_unit('Candy suspended bonbons',(-6.5,8.6,0))
for x,y,z,col in [(-8.2,10.8,3.72,'Teal'),(-4.8,10.7,3.38,'Yellow')]:
    uv('Giant polished bonbon',(x,y,z),(.46,.3,.31),M[col],24,16)
    for s in (-1,1):
        for j in range(4):
            o=uv('Giant folded sweet wrapper',(x+s*.62,y,z+(j-1.5)*.075),(.24,.07,.11),M[col],12,8)
            o.rotation_euler[1]=s*(j-1.5)*.2
    rod('Confection suspension',(x,y,z+.26),(x,y,4.74),.011,M['Gold'])

# DRINKS: labels on each bottle, fruit garnish, caps, outer shelves of juice
# cartons and a sculpted juice splash that reinforces the central giant orange.
GROUP='Rainbow drinks boutique'
merch_unit('Rainbow juice pavilion',(7,-4.3,0))
for level,(r,n) in enumerate([(1.72,37),(1.14,25),(.57,13)]):
    z=1.24+level*.47
    for j in range(n):
        a=j*math.tau/n+.08
        x=7+r*math.cos(a);y=-4.3+r*math.sin(a)
        col=['Raspberry','PeachJuice','LimeJuice','Teal','GrapeJuice'][j%5]
        # Original filled bottle silhouette avoids the washed-out uniformity of
        # a single reused bottle material; reusable bottles remain underneath.
        cyl('Colored juice bottle body',(x,y,z+.22),.073,.28,M[col],16)
        uv('Juice bottle shoulder',(x,y,z+.37),(.073,.073,.08),M[col],16,8)
        cyl('Juice bottle neck',(x,y,z+.42),.033,.09,M[col],12)
        cyl('Juice bottle cap',(x,y,z+.47),.038,.038,M['Gold'],12)
        cyl('Juice bottle paper label',(x,y,z+.22),.075,.13,M['Porcelain'],16)
        # Labels point to the outside edge of the display.
        o=text('SIPO',(x+.076*math.cos(a),y+.076*math.sin(a),z+.23),.047,M[col],extrude=.0007)
        o.rotation_euler[2]=a+math.pi/2
        o['preserve_scale']=True
        MERCH_STATS['originalPackagedProducts']+=1
for j in range(18):
    a=j*math.tau/18;r=1.85
    x=7+r*math.cos(a);y=-4.3+r*math.sin(a)
    # Each garnish is a distinct licensed fruit, tucked into the display edge.
    merch_food(['lemon','strawberry','grapes','apple'][j%4],(x,y,1.24),.18)
for j in range(7):
    a=j*math.tau/7
    end=(7+.75*math.cos(a),-4.3+.75*math.sin(a),2.9+(.1 if j%2 else .35))
    rod('Sculpted juice splash filament',(7+.40*math.cos(a),-4.3+.40*math.sin(a),2.75),end,.028,M['PeachJuice'])
    uv('Suspended juice splash droplet',end,(.07,.07,.13),M['PeachJuice'],16,10)
for index,(x,y) in enumerate([(4.25,-2.65),(9.75,-2.65)]):
    merch_unit('Juice carton tasting stand %d'%index,(x,y,0))
    cube('Juice tasting podium',(x,y,.60),(1.05,1.15,1.2),M['Orange'],.10)
    for level in range(3):
        zz=1.23+level*.52
        cube('Juice tasting shelf',(x,y,zz),(1.14,1.19,.06),M['Porcelain'])
        for j in range(3):
            for row in range(2):
                packaged_box(x-.32+j*.32,y-.24+row*.41,zz+.04,['PeachJuice','LimeJuice','Raspberry'][j],'SIP',.29)
    price_card('TASTE THE RAINBOW',(x,y-.615,1.01),1.13)
    coll('Juice tasting stand',(x,y,1.1),(1.2,1.25,2.2))
    MERCH_STATS['stockedDisplays']+=1

# FROZEN: full compartmented cabinets, front ventilation/grab handles,
# branded ice cream cartons and crystalline ice sculptures.  Fish are placed
# inside the cabinets below the existing clear sliding lids.
GROUP='Frost boutique merchandising'
# The former fish props sat on top of closed freezer lids; replace that
# implausible display with packaged stock visible through the clear lids.
for obj in list(scene.objects):
    p=obj.location
    if obj.name.startswith('Kenney fish') and -.6<p.x<2.6 and 9.5<p.y<9.8 and 1.79<p.z<1.82:
        bpy.data.objects.remove(obj,do_unlink=True)
merch_unit('Frozen glacier showcase',(1,10,0))
for i,dx in enumerate((-1.45,0,1.45)):
    x=1+dx
    cube('Freezer cold inner tray',(x,9.8,1.475),(1.18,1.46,.06),M['FrostWhite'])
    for split in (-.35,0,.35):cube('Freezer product basket divider',(x+split,9.8,1.585),(.018,1.35,.19),M['Chrome'])
    for k in range(3):
        for row in range(3):
            xx=x-.39+k*.39;yy=9.32+row*.46
            packaged_box(xx,yy,1.51,['Ice','Candy','Blue'][(k+row)%3],['ICE','POP','SNOW'][(k+row)%3],.21)
    for k in range(10):cube('Freezer ventilation flute',(x-.49+k*.109,8.991,1.23),(.032,.018,.18),M['IceDeep'])
    rod('Freezer sliding lid handle',(x-.25,9.20,1.81),(x+.25,9.20,1.81),.025,M['Chrome'])
    cube('Freezer chilled light bar',(x,8.97,1.60),(1.15,.035,.035),M['BlueLight'])
    text(['ICE CREAM','SNOW POPS','FROZEN JOY'][i],(x,8.965,1.40),.095,M['White'])
# Side towers use closed original packages so shelves are visibly full.
for index,(x,y) in enumerate([(-1.65,12.2),(3.55,12.2)]):
    merch_unit('Frost snow tower %d'%index,(x,y,0))
    cube('Frozen blue refrigerated tower',(x,y,1.64),(1.30,.95,3.28),M['IceDeep'],.09)
    cube('Frozen luminous refrigerator interior',(x,y-.49,1.69),(1.10,.035,2.96),M['FrostWhite'])
    for row in range(5):
        z=.24+row*.55
        cube('Freezer tower clear shelf',(x,y-.72,z),(1.18,.52,.045),M['Glass'])
        for col in range(4):packaged_box(x-.42+col*.28,y-.73,z+.04,['Ice','Candy','Blue','Purple'][(col+row)%4],'FROST',.23)
        cube('Refrigerator cyan shelf edge',(x,y-.99,z),(1.18,.025,.025),M['BlueLight'])
    for dx in (-.63,.63):rod('Freezer door polished frame',(x+dx,y-1.01,.10),(x+dx,y-1.01,3.28),.023,M['Chrome'])
    # Slim glass pane suggests refrigeration without hiding package colors.
    cube('Frozen tower clear door',(x,y-1.015,1.7),(1.18,.017,3.10),M['Glass'])
    rod('Frozen tower door handle',(x+.42,y-1.065,1.18),(x+.42,y-1.065,1.88),.029,M['Chrome'])
    price_card('A LITTLE FROSTY',(x,y-1.08,3.48),1.27)
    coll('Stocked freezer tower',(x,y-.38,1.73),(1.35,1.75,3.46))
    MERCH_STATS['stockedDisplays']+=1
# Tip each existing blunt crystal with a genuine faceted pointed cap.
merch_unit('Ice sculpture tips',(1,10,0))
for index in range(7):
    x=-.8+index*.58;y=11
    base=3.36+math.sin(index*2)*.22
    verts=[(x+.235*math.cos(a*math.tau/5),y+.235*math.sin(a*math.tau/5),base) for a in range(5)]
    verts.append((x+.04,y,base+.53))
    mesh=bpy.data.meshes.new('Pointed five-sided ice crystal');mesh.from_pydata(verts,[],[(j,(j+1)%5,5) for j in range(5)]+[(4,3,2,1,0)]);mesh.update()
    obj=bpy.data.objects.new('Cut crystal glacier point',mesh);bpy.context.collection.objects.link(obj);finish(obj,obj.name,M['FrostWhite'] if index%2 else M['Ice'])

# Explicit product-scale metadata is retained even for product components that
# already belong to a coherent fixture unit.
for obj in scene.objects:
    if obj.name.startswith(('French macaron almond shell','Macaron cream filling',
                            'Colorful loose jelly bean','Colored juice bottle body',
                            'Juice bottle shoulder','Juice bottle neck',
                            'Juice bottle cap','Juice bottle paper label')):
        obj['preserve_scale']=True

# Restore the generator's helper for modules executed after this one.
finish=_merch_finish
GROUP='Premium merchandising'
DATA.setdefault('artStatistics',{}).update(MERCH_STATS)
print('Premium boutique merchandise:',json.dumps(MERCH_STATS),flush=True)
