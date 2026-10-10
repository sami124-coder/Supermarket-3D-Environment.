"""Second art pass, executed inside build_supermarket before static consolidation.
Preserves the building, licensed groceries and existing runtime integration.
"""
GROUP='Fantasy art direction'
# Replace the generic checkerboard and flat central plaque with flowing enamel.
for o in list(scene.objects):
    if o.name.startswith(('Polished terrazzo tile','Floor brass inlay','Sipo suspended brand plaque','Sipo inner plaque','Sunny mascot','Mascot eye','Mascot rosy','Mascot happy','Mascot hanging')):
        bpy.data.objects.remove(o,do_unlink=True)
M['FloorCobalt']=mat('FloorCobalt','164BC4',.095,.32)
M['FloorPearl']=mat('FloorPearl','FFF0D4',.12,.22)
M['FloorTangerine']=mat('FloorTangerine','FF850A',.10,.25)
M['Candy']=mat('Candy','FC218B',.22,.12)
M['Ice']=mat('Ice','57DFFF',.18,.25)
M['Skin']=mat('Skin','F1B786',.4)
M['Cuff']=mat('Cuff','F7940A',.32)
cube('Continuous polished cobalt floor',(0,0,-.023),(48,44,.055),M['FloorCobalt'])
for r,w,ma in [(22,3,'FloorPearl'),(17.8,1.2,'FloorTangerine'),(15.9,2.5,'FloorPearl'),(11.8,.18,'Gold'),(10.8,2.2,'FloorPearl'),(7.5,.7,'FloorTangerine'),(6.4,1.25,'FloorPearl'),(4.8,.12,'Gold')]:
    # Rings stay within the footprint: outer sweeping arcs are clipped by walls.
    ring('Flowing atrium floor ribbon',r,r*.82,.009,w,.014,M[ma],(0,-1))
# Saturated luminous planetarium, rather than an unlit black disc.
p=M['Night'].node_tree.nodes['Principled BSDF'];p.inputs['Emission Color'].default_value=(.008,.025,.32,1);p.inputs['Emission Strength'].default_value=.7
spec=next(x for x in DATA['materials'] if x['name']=='SIPO_Night');spec.update(emission=[.008,.025,.32],emissionStrength=.7)
# Lobed brand silhouette, actually modelled, readable from below.
for x,z,r in [(-2.5,8.15,1.22),(-1.1,8.6,1.5),(.7,8.55,1.48),(2.4,8.05,1.27)]:
    uv('Brand cloud gold rim',(x,-3.43,z),(r,.27,r*.78),M['WarmLight'],32,16)
    uv('Brand cloud orange enamel',(x,-3.69,z),(r*.95,.16,r*.735),M['Orange'],32,16)
# Move brand letters in front of the new cloud silhouette.
for o in scene.objects:
    if o.type=='FONT' and o.data.body=='Sipo' and o.location.y>-10:o.location.y=-3.89

def mascot(x,y,z,s=1,color='Orange',chef=False):
    """Original friendly orbit bear with oversized glassy eyes and soft paws."""
    global GROUP
    GROUP='Original orbit bear mascots'
    def ball(n,p,d,m):return uv(n,(x+p[0]*s,y+p[1]*s,z+p[2]*s),tuple(v*s for v in d),M[m],24,16)
    ball('Bear body',(0,.1,-.9),(.65,.42,.76),color)
    for dx in (-.68,.68):
        ball('Bear round ears',(dx,0,.61),(.39,.28,.43),color)
        ball('Bear inner ear',(dx,-.25,.62),(.22,.045,.26),'Pink')
        ball('Bear waving paws',(dx*1.3,-.06,-.65),(.29,.31,.42),'Cream')
        ball('Bear boots',(dx*.6,-.1,-1.48),(.31,.42,.23),'Cream')
    ball('Bear head',(0,0,0),(.86,.52,.85),'Cream')
    for dx in (-.34,.34):
        ball('Bear cobalt eye rim',(dx,-.46,.12),(.29,.1,.35),'Blue')
        ball('Bear glossy eye',(dx,-.54,.12),(.215,.075,.265),'Black')
        ball('Bear eye highlight',(dx-.065,-.604,.23),(.074,.025,.085),'WhiteLight')
        ball('Bear cheek',(dx*1.65,-.43,-.26),(.14,.042,.072),'Pink')
    ball('Bear nose',(0,-.54,-.2),(.10,.07,.075),'Navy')
    ball('Bear smile',(0,-.51,-.4),(.19,.065,.14),'Pink')
    if chef:
        ball('Chef hat brim',(0,0,.82),(.8,.42,.15),'White')
        for dx in (-.43,0,.43):ball('Chef hat puff',(dx,0,1.12),(.38,.38,.4),'White')
mascot(-6,-3.4,8.6,1.35)
mascot(1.9,-1.3,2.25,.5)
# Layered gallery fascia and repeated vines give the open volume depth.
GROUP='Gallery ornament'
for x in (-14,14):
    cube('Gallery continuous light',(x,-3.5,5.34),(.07,36.5,.065),M['WarmLight'])
    for y in range(-18,15,3):
        for j in range(3):
            xx=x+(-.08 if x<0 else .08); yy=y+j*.26
            for k in range(7):
                uv('Trailing gallery ivy',(xx+math.sin(k)*.12,yy,5.45-k*.19),(.12,.07,.17),M['LeafLight'] if k%3==0 else M['Leaf'],10,6)

def halo(label,x,y,z,r,color,subtitle):
    global GROUP
    GROUP='Themed department halos'
    ring(label+' sculpted halo',r,r,z,.3,.65,M[color],(x,y))
    for zz in (z-.34,z+.34):torus(label+' luminous edge',(x,y,zz),r,.035,M['WarmLight'])
    text(label,(x,y-r-.05,z),min(.48,r*.21),M['SignWhite'])
    text(subtitle,(x,y-r-.065,z-.24),.105,M['White'])
    light(label+' colored island wash',(x,y,z-.48),'FFDABD',360,3,unity_intensity=1.1,ran=7)

def island(x,y,r,color):
    cyl('Sculpted round display plinth',(x,y,.56),r,1.12,M[color],64)
    cyl('Pearl display counter',(x,y,1.15),r+.05,.12,M['Cream'],64)
    for z in (.12,1.06):torus('Display luminous piping',(x,y,z),r+.01,.024,M['WarmLight'])
    coll('Themed display island',(x,y,.62),(r*2,r*2,1.24))

def lollipop(x,y,z,r,color):
    rod('Giant candy stick',(x,y,.9),(x,y,z),.075,M['White'])
    o=torus('Candy outer frosting',(x,y,z),r,.14,M['White']);o.rotation_euler[0]=math.pi/2
    uv('Candy enamel disc',(x,y,z),(r,.14,r),M[color],32,16)
    points=[]
    for i in range(100):
        a=i*.17;rr=r*.9*i/100;points.append((x+rr*math.cos(a),y-.15,z+rr*math.sin(a)))
    for a,b in zip(points,points[1:]):rod('Candy sugar spiral',a,b,.034,M['White'])

# Produce: abundant raised fruit baskets, flowers and a luminous garden crown.
GROUP='Enchanted produce'
halo('FRESH PRODUCE',-10,1,5.1,3.75,'Green','THE ENCHANTED GARDEN')
for a in range(12):
    t=a*math.tau/12;x=-10+3.0*math.cos(t);y=1+3.0*math.sin(t)
    for k in range(5):food(['apple','pear','lemon','tomato','strawberry','grapes'][a%6],(x+random.uniform(-.2,.2),y+random.uniform(-.2,.2),.95+k*.075),.38)
    uv('Garden flower heart',(x,y,3.7),(.10,.10,.1),M['Yellow'],12,8)
    for j in range(5):
        ang=j*math.tau/5;uv('Garden flower petals',(x+.16*math.cos(ang),y,3.7+.16*math.sin(ang)),(.13,.065,.14),M['Pink'],12,8)
mascot(-10,1,5.95,.62,'Green')
# Bakery: candy-glazed doughnut arch, cake tiers, chef mascot and warm crown.
GROUP='Patisserie'
halo('BAKERY',-18,11,4.55,3.3,'Orange','BREAD • CAKES • LITTLE DELIGHTS')
for x in (-20.2,-15.8):
    o=torus('Giant baked donut',(x,10.8,2.9),.69,.24,M['Oak']);o.rotation_euler[0]=math.pi/2
    o=torus('Donut strawberry glaze',(x,10.57,2.9),.69,.12,M['Candy']);o.rotation_euler[0]=math.pi/2
    for j in range(12):
        a=j*math.tau/12
        rod('Donut sugar sprinkle',(x+.68*math.cos(a),10.43,2.9+.68*math.sin(a)),(x+.68*math.cos(a)+.08,10.43,2.96+.68*math.sin(a)),.018,M['Yellow'] if j%2 else M['Ice'])
for x in (-18.8,-17.5,-16.2):
    cyl('Patisserie tier stand',(x,10.3,1.62),.47,.15,M['Gold'])
    food('cakeBirthday',(x,10.3,1.71),.8)
mascot(-18,12,3.05,.7,'Orange',True)
# Candy garden in front of the rear snack department.
GROUP='Candy wonderland'
island(-6.5,8.6,2.1,'Candy');halo('SNACKS',-6.5,8.6,4.9,2.65,'Candy','THE CANDY COSMOS')
for dx,dy,z,r,col in [(-1,.1,3.0,.65,'Candy'),(.1,.7,3.55,.83,'Purple'),(1,-.1,2.8,.6,'Teal')]:lollipop(-6.5+dx,8.6+dy,z,r,col)
for i in range(42):
    a=i*2.4;r=1.2+(i%3)*.25
    food(['donutChocolate','cupcake','cookieChocolate'][i%3],(-6.5+r*math.cos(a),8.6+r*math.sin(a),1.23),.35)
# Circular drinks bar with vivid custom label collars on reusable bottles.
GROUP='Rainbow drinks'
island(7,-4.3,2.1,'Orange');halo('DRINKS',7,-4.3,4.5,2.5,'Orange','SIP A LITTLE SUNSHINE')
for level,r,n in [(0,1.8,32),(1,1.28,23),(2,.73,14)]:
    z=1.22+level*.47
    if level:cyl('Drinks stepped riser',(7,-4.3,z-.2),r+.17,.4,M['Orange'])
    for i in range(n):
        a=i*math.tau/n;x=7+r*math.cos(a);y=-4.3+r*math.sin(a)
        food('sodaBottle',(x,y,z),.46)
        cyl('Rainbow bottle sleeve',(x,y,z+.18),.075,.15,M[['Candy','Teal','Yellow','Blue','Green'][i%5]],12)
uv('Giant orange juice fruit',(7,-4.3,3.05),(.55,.55,.55),M['Orange'])
rod('Giant bendy straw',(7,-4.3,3.1),(7.35,-4.3,3.9),.06,M['White'])
# Frozen: icy portal, crystal peaks and decorative snowflakes around a freezer island.
GROUP='Frozen aurora'
island(1,10,2.05,'Blue');halo('FROZEN',1,10,4.8,2.6,'Blue','THE FROSTY PLANET')
for dx in (-1.45,0,1.45):
    cube('Icy freezer cabinet',(1+dx,9.8,1.4),(1.3,1.6,.65),M['Ice'],.1)
    cube('Freezer glazed lid',(1+dx,9.8,1.76),(1.19,1.48,.05),M['Glass'],.02)
    food('fish',(1+dx,9.65,1.8),.65)
for i in range(7):
    x=-.8+i*.58
    o=cyl('Faceted ice crystal',(x,11,2.4+random.random()*.3),.22,1.7+random.random(),M['Ice'],5);o.rotation_euler[1]=random.uniform(-.25,.25)
for x,z in [(-.3,3.7),(2.3,3.4),(1,4)]:
    for j in range(6):
        a=j*math.tau/6
        rod('Snowflake arm',(x,9.6,z),(x+.42*math.cos(a),9.6,z+.42*math.sin(a)),.025,M['WhiteLight'])
        for s in (-1,1):
            b=a+s*.7
            rod('Snowflake twig',(x+.28*math.cos(a),9.6,z+.28*math.sin(a)),(x+.28*math.cos(a)-.14*math.cos(b),9.6,z+.28*math.sin(a)-.14*math.sin(b)),.015,M['WhiteLight'])
# Clear two existing upper side bays for dedicated kitchen and gym art.
for o in list(scene.objects):
    if o.type=='MESH' and 5.8<o.location.z<9.4 and abs(o.location.x)>16 and -10<o.location.y<10:
        if o.name.startswith(('Shelf','Retail','Price','Food_')) or o.get('sipo_group')=='Licensed groceries':bpy.data.objects.remove(o,do_unlink=True)
DATA['colliders']=[c for c in DATA['colliders'] if not(c['name']=='Stocked shelf' and c['position'][1]>6 and abs(c['position'][0])>16 and abs(c['position'][2])<10)]

def furniture(name,loc,size):
    """Reuse the original licensed furniture glTF, preserving its materials."""
    path=ROOT/'Assets/ThirdParty/KenneyFurnitureKit/Source'/(name+'.glb')
    before=set(scene.objects);bpy.ops.import_scene.gltf(filepath=str(path))
    objects=[o for o in scene.objects if o not in before]
    bpy.context.view_layer.update()
    meshes=[o for o in objects if o.type=='MESH']
    points=[o.matrix_world@v.co for o in meshes for v in o.data.vertices]
    lo=Vector(tuple(min(v[i] for v in points) for i in range(3)));hi=Vector(tuple(max(v[i] for v in points) for i in range(3)))
    center=Vector(((lo.x+hi.x)/2,(lo.y+hi.y)/2,lo.z));factor=size/max(hi-lo)
    for o in meshes:
        mesh=o.data.copy();matrix=o.matrix_world.copy();o.parent=None;o.matrix_world.identity();o.data=mesh
        for v in mesh.vertices:v.co=(matrix@v.co-center)*factor+Vector(loc)
        finish(o,'Licensed kitchen '+name)
    for o in objects:
        if o.type!='MESH':bpy.data.objects.remove(o,do_unlink=True)
GROUP='Show kitchen'
halo('KITCHEN',-19,0,10.2,3.45,'Teal','COOK UP SOME JOY')
cube('Kitchen backsplash',(-19,2.3,7.7),(7,.16,3.7),M['Teal'],.15)
text('KITCHEN',(-19,2.18,8.6),.66,M['SignWhite'])
for i,name in enumerate(['kitchenFridgeLarge','kitchenCabinetDrawer','kitchenSink','kitchenCabinet']):furniture(name,(-21.5+i*1.6,1.6,5.81),1.5 if i else 2.2)
cube('Cooking demonstration island',(-19,-1.5,6.45),(5.7,1.7,1.3),M['Orange'],.16)
cube('Cooking stone worktop',(-19,-1.5,7.14),(5.9,1.9,.12),M['Cream'],.05)
coll('Kitchen demo counter',(-19,-1.5,6.5),(5.9,1.9,1.4))
for x in (-20,-19.3):
    for y in (-1.9,-1.2):torus('Induction cooking ring',(x,y,7.22),.22,.025,M['Black'])
furniture('kitchenCoffeeMachine',(-17.7,-1.5,7.21),.7)
furniture('toaster',(-18.5,1.6,7.3),.55)
for x in (-20.2,-18.4,-16.8):
    cyl('Copper pan hanging hook',(x,2.01,8.4),.04,.4,M['Gold'])
    o=cyl('Copper display pan',(x,1.98,8.04),.29,.1,M['Gold']);o.rotation_euler[0]=math.pi/2
# Gym with static sculpted treadmills, weight rack, yoga mat and exercise balls.
GROUP='Playful gym'
halo('GYM',19,0,10.2,3.45,'Purple','MOVE • SMILE • REPEAT')
cube('Gym feature wall',(19,2.3,7.7),(7,.16,3.7),M['Purple'],.15)
text('GYM',(19,2.17,8.6),.8,M['SignWhite'])
for x in (17,19):
    cube('Treadmill colorful base',(x,-.6,6.02),(1.4,2.7,.35),M['Teal'],.14)
    cube('Treadmill belt',(x,-.6,6.22),(1.06,2.2,.065),M['Navy'],.05)
    for dx in (-.53,.53):rod('Treadmill handle frame',(x+dx,.25,6.18),(x+dx,.6,7.45),.06,M['Orange'])
    cube('Treadmill display console',(x,.61,7.45),(1.27,.45,.26),M['Orange'],.08)
    cube('Treadmill screen',(x,.38,7.49),(.61,.04,.19),M['BlueLight'],.03)
    coll('Static treadmill',(x,-.6,6.55),(1.45,2.7,1.5))
for z in (6.25,6.85):
    cube('Weight rack',(21.5,.8,z),(1.8,.55,.1),M['Gold'])
    for x in (20.9,21.5,22.1):
        rod('Dumbbell handle',(x-.15,.8,z+.15),(x+.15,.8,z+.15),.05,M['Chrome'])
        for dx in (-.17,.17):
            o=cyl('Colorful dumbbell',(x+dx,.8,z+.15),.15,.12,M['Candy']);o.rotation_euler[1]=math.pi/2
cube('Yoga mat',(21,-2,5.83),(1.3,2.5,.045),M['Candy'],.08)
uv('Gym exercise ball',(21.5,-1.8,6.38),(.55,)*3,M['Yellow'],32,20)
DATA['departments'].extend([{'name':'Kitchen','position':[-19,5.8,0],'size':[7,4,7],'color':[.1,.7,.7]},{'name':'Gym','position':[19,5.8,0],'size':[7,4,7],'color':[.5,.2,.8]}])
# Checkout gets its own floating crown and friendly cashier mascot.
GROUP='Checkout identity'
halo('CHECKOUT',14,-10.5,4.85,5.3,'Teal','THANK YOU • SEE YOU SOON')
mascot(18,-9.5,2.65,.6,'Teal')
# Art-directed local lights supplement the preserved architectural lighting.
light('Kitchen studio',(-19,-1,10),'FFF0D6',900,5,unity_intensity=2,ran=9)
light('Gym studio',(19,-1,10),'E5DBFF',900,5,unity_intensity=2,ran=9)
# Keep orange saturated under the warm architectural lighting.
p=M['Orange'].node_tree.nodes['Principled BSDF'];p.inputs['Base Color'].default_value=(*(lin(v) for v in rgb('FF6206')),1);p.inputs['Metallic'].default_value=.08
next(x for x in DATA['materials'] if x['name']=='SIPO_Orange').update(color=list(rgb('FF6206')),metallic=.08)
for key,strength in [('WarmLight',2),('SignWhite',.7)]:
    M[key].node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value=strength
    next(x for x in DATA['materials'] if x['name']==M[key].name)['emissionStrength']=strength
for o in scene.objects:
    if o.type=='LIGHT':o.data.energy*=.7
# Remove the older, lower produce banner now that a larger garden halo exists.
for o in list(scene.objects):
    if o.name.startswith(('Fresh produce suspended sign','Fresh garden light')) or (o.type=='FONT' and o.data.body in ('FRESH PRODUCE','GROWN WITH LOVE') and o.location.z<4.3):bpy.data.objects.remove(o,do_unlink=True)
GROUP='Show kitchen'
for x,y in [(-20,-1.9),(-19.3,-1.2)]:
    cyl('Copper cooking pot',(x,y,7.37),.23,.29,M['Gold'],32)
    cyl('Cooking pot lid',(x,y,7.53),.245,.045,M['Chrome'],32)
    uv('Pot lid grip',(x,y,7.6),(.07,.045,.04),M['Navy'])
    for dx in (-.3,.3):rod('Pot handle',(x+dx*.7,y,7.4),(x+dx,y,7.4),.035,M['Navy'])
for i in range(5):food(['carrot','tomato','broccoli','loaf','lemon'][i],(-18.7+i*.24,-1.95,7.22),.23)
cube('Chef cutting board',(-18.3,-1.9,7.22),(1.2,.65,.045),M['Wood'],.035)
cube('Orange extraction canopy',(-19,1.5,9),(3.3,1.25,.5),M['Orange'],.14)
for x in (-20,-19,-18):cyl('Extractor light',(x,1.4,8.73),.1,.025,M['WhiteLight'])
# Open the bakery frontage: old generic shelving obscured the new display.
for o in list(scene.objects):
    p=o.location
    if p.x<-17 and 7.4<p.y<9.65 and p.z<3.5 and o.get('sipo_group') in ('Furniture','Licensed groceries'):
        bpy.data.objects.remove(o,do_unlink=True)
    elif -22<p.x<-16 and 8<p.y<13 and p.z>.8 and o.get('sipo_group')=='Botanical garden':
        bpy.data.objects.remove(o,do_unlink=True)
DATA['colliders']=[c for c in DATA['colliders'] if not(c['name']=='Stocked shelf' and c['position'][0]<-17 and -9.65<c['position'][2]<-7.4 and c['position'][1]<3.5)]
# Stagger the middle checkout around the existing structural column.
for o in scene.objects:
    if o.get('sipo_group')=='Furniture' and 12.7<o.location.x<15.3 and -13.1<o.location.y<-9.2 and o.location.z<4.3:
        o.location.y+=4
for c in DATA['colliders']:
    if c['name']=='Checkout counter' and c['position'][0]==14:c['position'][2]-=4
GROUP='Checkout identity'
text('CHECKOUT',(17,-14.2,4.15),.52,M['SignWhite'])
for x,y in [(10,-11),(14,-7),(18,-11)]:
    for j in range(3):food(['apple','carton','loaf'][j],(x,y-.6+j*.5,1.53),.3)
    cube('Checkout lower trim',(x,y-1.91,.18),(2.2,.025,.045),M['WarmLight'])
# Static showroom boundaries supplement the preserved building collision layout.
coll('Kitchen feature wall',(-19,2.3,7.7),(7,.18,3.7))
coll('Kitchen back cabinets',(-19,1.6,6.5),(7,1.3,1.4))
coll('Gym feature wall',(19,2.3,7.7),(7,.18,3.7))
coll('Gym weight rack',(21.5,.8,6.5),(1.8,.65,1.4))
# Art-direct placed copies of the CC0 palette toward richer confectionery colors.
# Retained source GLBs/FBXs are unchanged. The input palette is intentionally pastel;
# applying a contrast curve to the placed materials gives stronger fruit/food identity.
for material in bpy.data.materials:
    if material.name.startswith('SIPO_') or not material.use_nodes:continue
    p=material.node_tree.nodes.get('Principled BSDF')
    if not p:continue
    c=p.inputs['Base Color'].default_value[:3]
    p.inputs['Base Color'].default_value=(*(lin(v) for v in c),1)
    p.inputs['Metallic'].default_value=0
    p.inputs['Roughness'].default_value=.38
