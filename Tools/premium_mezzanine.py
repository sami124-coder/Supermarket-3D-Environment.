"""Premium upper-gallery art pass; executed in the existing builder's namespace.

All coordinates are the original 48 x 44 m building coordinates. Architectural
elements follow the later building expansion. Furnishing groups retain their
local proportions through art_unit/art_anchor annotations. No runtime systems.
"""

GROUP = 'Premium mezzanine architecture'
for _key, _hex, _rough, _metal in [
    ('GalleryTurquoise', '087C8D', .22, .15),
    ('GalleryRose', 'F45E96', .24, .12),
    ('GalleryLavender', 'AB8DEB', .28, .10),
    ('GalleryIvory', 'F9E7C4', .26, .14),
    ('GalleryWalnut', '673B25', .38, .02),
    ('GalleryVelvet', 'F67733', .48, 0),
]:
    M[_key] = mat(_key, _hex, _rough, _metal)


def pm_tag_since(before, unit, anchor):
    for obj in set(scene.objects) - before:
        if obj.type in ('MESH', 'FONT', 'CURVE'):
            obj['art_unit'] = unit
            obj['art_anchor'] = list(anchor)


_PM_FURNITURE = {}


def pm_furniture(name, loc, size, rotation=0):
    """Import each CC0 furniture type once, then instance its local mesh data."""
    if name not in _PM_FURNITURE:
        before = set(scene.objects)
        furniture(name, (0, 0, 0), 1)
        created = list(set(scene.objects) - before)
        _PM_FURNITURE[name] = [(o.data, o.name) for o in created if o.type == 'MESH']
        for obj in created:
            bpy.data.objects.remove(obj, do_unlink=True)
    result = []
    for mesh, label in _PM_FURNITURE[name]:
        obj = bpy.data.objects.new('Gallery CC0 ' + name, mesh)
        bpy.context.collection.objects.link(obj)
        obj.location = loc
        obj.scale = (size,) * 3
        obj.rotation_euler[2] = rotation
        finish(obj, 'Gallery CC0 ' + name)
        result.append(obj)
    return result


def pm_arch(name, x, y, bottom, width, shoulder, rise, ma, thickness=.065):
    """A dimensional, continuous architectural arch with real return depth."""
    pts = [(x-width/2, y, bottom), (x-width/2, y, shoulder)]
    for j in range(33):
        a = math.pi - j*math.pi/32
        pts.append((x+width/2*math.cos(a), y, shoulder+rise*math.sin(a)))
    pts.append((x+width/2, y, bottom))
    for a, b in zip(pts, pts[1:]):
        rod(name, a, b, thickness, ma)


def pm_pendant(x, y, ceiling=11.8, bottom=9.0, color='Orange', r=.38):
    rod('Gallery pendant braided drop', (x,y,bottom+.3), (x,y,ceiling), .018, M['Gold'])
    uv('Gallery opaline pendant diffuser', (x,y,bottom), (r*.82,r*.82,r*.64), M['WhiteLight'], 24,16)
    o=cyl('Gallery spun enamel lamp shade',(x,y,bottom+.19),r,.24,M[color],32)
    torus('Gallery pendant brass rolled lip',(x,y,bottom+.075),r,.027,M['Gold'])


def pm_cup(x, y, z, color='Cream'):
    cyl('Café ceramic cup',(x,y,z+.085),.085,.17,M[color],24)
    cyl('Café espresso surface',(x,y,z+.172),.072,.008,M['GalleryWalnut'],24)
    o=torus('Café cup handle',(x+.095,y,z+.09),.055,.013,M[color]);o.rotation_euler[0]=math.pi/2
    cyl('Café porcelain saucer',(x,y,z+.011),.14,.021,M['Cream'],24)


def pm_table(x, y, z=5.81, color='Orange', unit='table'):
    before=set(scene.objects)
    pm_furniture('tableRound',(x,y,z),1.05)
    # Four solid seating positions; restrained gold legs and soft upholstered pads.
    for j in range(3):
        a=j*math.tau/3+math.pi/6
        xx=x+1.02*math.cos(a); yy=y+1.02*math.sin(a)
        pm_furniture('chairRounded',(xx,yy,z),.88,a+math.pi/2)
        uv('Gallery velvet seat cushion',(xx,yy,z+.46),(.25,.25,.055),M[color],20,12)
    pm_cup(x-.2,y-.17,z+.82)
    pm_cup(x+.19,y+.11,z+.82,'GalleryRose')
    cyl('Café tiny vase',(x+.21,y-.2,z+.92),.056,.2,M['Teal'],16)
    for j in range(3):
        a=j*math.tau/3
        rod('Café flower stem',(x+.21,y-.2,z+.94),(x+.21+.05*math.cos(a),y-.2+.05*math.sin(a),z+1.13),.008,M['Leaf'])
        uv('Café daisy flower',(x+.21+.05*math.cos(a),y-.2+.05*math.sin(a),z+1.13),(.07,.07,.025),M['Yellow'],12,8)
    food('croissant',(x-.12,y+.18,z+.83),.27)
    pm_tag_since(before,'Gallery seating '+unit,(x,y,z))
    coll('Gallery café table and chairs',(x,y,z+.5),(2.6,2.6,1))


def pm_showcase(x,y,z,width,color,theme):
    """Open, lit wood-and-enamel display wall; art directed by product family."""
    global GROUP
    GROUP='Premium gallery display cabinets'
    before=set(scene.objects)
    cube('Gallery cabinet curved backing',(x,y+.32,z+1.35),(width,.16,2.72),M[color],.12)
    for xx in (x-width/2,x+width/2):
        cube('Gallery brass case stile',(xx,y,z+1.35),(.08,.8,2.75),M['Gold'],.018)
    for row in range(4):
        zz=z+.28+row*.63
        cube('Gallery floating display shelf',(x,y,zz),(width,.8,.075),M['GalleryIvory'],.018)
        cube('Gallery shelf integrated light',(x,y-.33,zz-.04),(width-.1,.034,.026),M['WarmLight'])
        for col in range(int(width/.5)):
            xx=x-width/2+.3+col*.5
            if theme=='bakery':
                food(['croissant','cupcake','muffin','donutChocolate','cookieChocolate','bread'][(row+col//2)%6],(xx,y-.07,zz+.045),.36)
            elif theme=='botanica':
                cyl('Boutique glazed herb pot',(xx,y-.05,zz+.16),.15,.23,M[['Teal','Cream','Orange'][(col+row)%3]],16)
                for j in range(5):
                    a=j*2.4
                    o=uv('Boutique herb leaves',(xx+.1*math.cos(a),y-.05+.1*math.sin(a),zz+.32),(.065,.025,.18),M['LeafLight'] if j%2 else M['Leaf'],12,8)
                    o.rotation_euler=(.5*math.cos(a),.5*math.sin(a),a)
            elif theme=='home':
                if (col+row)%2:
                    for k in range(4):cyl('Home studio ceramic bowl stack',(xx,y-.08,zz+.055+k*.045),.18-k*.012,.06,M[['Cream','Teal','GalleryRose'][row%3]],24)
                else:
                    uv('Home studio glazed vase',(xx,y-.1,zz+.2),(.12,.12,.19),M[['Teal','Cream','Orange'][row%3]],20,12)
                    cyl('Home studio vase neck',(xx,y-.1,zz+.37),.057,.10,M[['Teal','Cream','Orange'][row%3]],16)
            else:
                # Colorful toy boxes feature dimensional inset windows and a star.
                color2=['Candy','Blue','Teal','Yellow','Purple'][(col+row)%5]
                cube('Toy boutique printed gift box',(xx,y-.02,zz+.2),(.37,.35,.34),M[color2],.027)
                cube('Toy gift box ivory label',(xx,y-.205,zz+.21),(.21,.012,.18),M['Cream'],.014)
                uv('Toy gift box illustrated moon',(xx-.018,y-.219,zz+.22),(.054,.008,.054),M['Orange'],12,8)
                cube('Toy gift box foil stripe',(xx+.11,y-.215,zz+.2),(.025,.008,.32),M['Gold'])
    pm_tag_since(before,'Gallery showcase '+str((x,y,z)),(x,y,z))
    coll('Gallery stocked display cabinet',(x,y,z+1.4),(width+.15,.85,2.8))


# Replace the old straight upper signs and generic grocery shelves. The lower
# market and every licensed source file stay untouched.
for _o in list(scene.objects):
    _upper_rear = _o.location.z>5.8 and _o.location.y>19
    if _upper_rear and (
        _o.name.startswith(('Department ','Sign light ','Shelf ','Retail shelf','Price strip','Price ticket'))
        or _o.get('sipo_group')=='Licensed groceries'
        or (_o.type=='FONT' and _o.data.body in ['HOME & LIVING','LITTLE WONDERS','EVERYDAY JOY','TOYS','THE GREEN ROOM'])
    ):
        bpy.data.objects.remove(_o,do_unlink=True)
DATA['colliders']=[c for c in DATA['colliders'] if not(c['name']=='Stocked shelf' and c['position'][1]>6 and c['position'][2]<-19)]

_PM_STORES=[
    (-18,'HOME STUDIO','BEAUTIFUL EVERYDAY OBJECTS','GalleryTurquoise','home'),
    (-9,'LITTLE WONDERS','BIG DREAMS FOR LITTLE PEOPLE','GalleryRose','toys'),
    (0,'SUNSHINE CAFÉ','COFFEE • CAKES • HAPPY MOMENTS','Orange','bakery'),
    (9,'PLAY PLANET','A UNIVERSE OF IMAGINATION','Blue','toys'),
    (18,'BOTANICA','A LITTLE GARDEN OF YOUR OWN','Green','botanica'),
]
for _idx,(_x,_title,_sub,_color,_theme) in enumerate(_PM_STORES):
    GROUP='Premium mezzanine storefronts'
    # Layered entrance fascia projects into the gallery without closing it.
    cube('Boutique '+_title+' dimensional frieze',(_x,18.9,10.65),(8.35,.8,1.22),M[_color],.13)
    cube('Boutique '+_title+' brass cornice',(_x,18.9,11.33),(8.5,.98,.10),M['Gold'],.025)
    cube('Boutique '+_title+' illuminated soffit',(_x,18.52,10.06),(8.10,.065,.055),M['WarmLight'])
    text(_title,(_x,18.46,10.75),.53 if len(_title)<13 else .44,M['SignWhite'],extrude=.018)
    text(_sub,(_x,18.45,10.35),.113,M['Cream'])
    cube('Boutique '+_title+' rear feature wall',(_x,21.8,8.24),(8,.12,4.75),M[_color],.035)
    # Deep portals with repeated polished fins cast rich oblique shadows.
    for _side in (-1,1):
        _xx=_x+_side*3.94
        cube('Gallery rounded portal pillar',(_xx,19.85,8.0),(.27,3.65,4.4),M['GalleryIvory'],.07)
        for _yy in (18.1,18.35,18.60):
            cube('Gallery brass portal fin',(_xx,_yy,8.1),(.055,.06,4.5),M['Gold'],.015)
        for _zz in (5.94,9.72):
            cube('Gallery fluted column collar',(_xx,18.38,_zz),(.44,.72,.12),M['Gold'],.02)
    pm_arch('Boutique illuminated arch',_x,18.48,5.88,7.6,9.1,.93,M['WarmLight'],.036)
    pm_arch('Boutique outer brass arch',_x,18.56,5.88,7.84,9.13,1.08,M['Gold'],.062)
    # Scalloped valance and angled canopy: a real awning, not a flat sign.
    for _j in range(20):
        _xx=_x-3.72+_j*.392
        _awning=cube('Boutique striped awning',(_xx,18.64,9.82),(.392,1.05,.10),M['Cream'] if _j%2 else M[_color],.016)
        _awning.rotation_euler[0]=.22
        uv('Boutique soft scalloped valance',(_xx,18.12,9.61),(.196,.075,.15),M['Cream'] if _j%2 else M[_color],16,8)
    cube('Boutique marble threshold',(_x,18.6,5.823),(7.6,.75,.025),M['GalleryIvory'])
    for _dx in (-2.03,2.03):
        pm_showcase(_x+_dx,21.10,5.81,3.1,_color,_theme)
    for _dx in (-2.2,2.2):pm_pendant(_x+_dx,19.9,12.2,9.25,_color,.31)
    light('Boutique '+_title+' window lighting',(_x,19.2,10),'FFE3BB',430,3.5,target=(_x,21,7.2),unity_intensity=1.2,ran=7)
    # Tall polished planters flank the portal but leave the gallery walkway open.
    for _dx in (-3.45,3.45):
        _b=set(scene.objects);planter(_x+_dx,18.6,5.81,.64)
        pm_tag_since(_b,'Boutique portal plant '+str((_x,_dx)),(_x+_dx,18.6,5.81))

# Shop-window storytelling: staged homeware, a toy-building city, a real café
# servery and a greenhouse vignette are readable across the open atrium.
GROUP='Gallery boutique vignettes'
_b=set(scene.objects)
cube('Home studio display rug',(-18,19.45,5.85),(3.3,1.45,.035),M['GalleryRose'],.1)
pm_furniture('tableRound',(-18.3,19.5,5.87),1.2)
pm_furniture('chairRounded',(-19.7,19.5,5.84),1.03,.6)
cyl('Home studio lamp brass base',(-16.9,19.4,5.88),.25,.08,M['Gold'])
rod('Home studio floor lamp stem',(-16.9,19.4,5.92),(-16.9,19.4,7.8),.026,M['Gold'])
uv('Home studio opal lamp',(-16.9,19.4,7.75),(.4,.4,.42),M['WhiteLight'],24,16)
food('honey',(-18.3,19.5,6.82),.27)
pm_tag_since(_b,'Home studio window vignette',(-18,19.5,5.81))
coll('Home studio window furniture',(-18,19.5,6.4),(3.6,1.6,1.2))

for _x,_color in [(-9,'GalleryRose'),(9,'Blue')]:
    _b=set(scene.objects)
    cyl('Toy planet presentation island',(_x,19.6,6.22),1.35,.82,M[_color],64)
    cyl('Toy planet snowy stage',(_x,19.6,6.67),1.39,.08,M['Cream'],64)
    for _j in range(12):
        _a=_j*2.4;_r=.24+(_j%3)*.31
        _xx=_x+math.cos(_a)*_r;_yy=19.6+math.sin(_a)*_r;_h=.23+(_j%4)*.2
        cube('Toy miniature city building',(_xx,_yy,6.72+_h/2),(.29,.31,_h),M[['Yellow','Candy','Teal','Orange'][_j%4]],.025)
        for _k in range(1+_j%3):
            cube('Toy city tiny window',(_xx,_yy-.161,6.81+_k*.14),(.10,.009,.075),M['WhiteLight'],.007)
    # Curved toy-rail loop, glossy wooden wagons and oversized stacking hoops.
    torus('Toy city railway loop',(_x,19.6,6.745),1.12,.025,M['Gold'],.70)
    for _j in range(4):
        _a=3.1+_j*.34;_xx=_x+1.12*math.cos(_a);_yy=19.6+.78*math.sin(_a)
        _o=cube('Toy wooden train wagon',(_xx,_yy,6.87),(.22,.33,.19),M[['Orange','Teal','Candy','Yellow'][_j]],.035);_o.rotation_euler[2]=_a
        for _s in (-1,1):uv('Toy train wheel',(_xx+_s*.105,_yy,6.80),(.035,.08,.08),M['Navy'],12,8)
    pm_tag_since(_b,'Toy city window '+str(_x),(_x,19.6,5.81))
    coll('Toy boutique display island',(_x,19.6,6.5),(2.8,2.8,1.4))

_b=set(scene.objects)
cube('Sunshine café fluted bar',(0,19.1,6.35),(5.4,1.0,1.07),M['GalleryWalnut'],.075)
for _x in [i*.19-2.47 for i in range(27)]:
    rod('Sunshine café vertical oak fluting',(_x,18.56,5.93),(_x,18.56,6.75),.025,M['Oak'])
cube('Sunshine café marble counter',(0,19.1,6.94),(5.55,1.14,.13),M['Cream'],.055)
pm_furniture('kitchenCoffeeMachine',(1.75,19.05,7.015),.86)
for _x in (-2,-1.45,-.90):
    cyl('Café cake pedestal',(_x,19.1,7.06),.24,.08,M['Gold'],32)
    food('cakeBirthday',(_x,19.1,7.11),.4)
for _x in (.05,.35,.65):pm_cup(_x,18.9,7.02)
text('COFFEE & CAKE',(0,18.54,6.47),.24,M['Cream'])
pm_tag_since(_b,'Sunshine cafe servery',(0,19.1,5.81))
coll('Sunshine café servery',(0,19.1,6.45),(5.5,1.15,1.3))

_b=set(scene.objects)
cube('Botanica stepped plant bench',(18,19.6,6.15),(4.5,1.6,.7),M['Oak'],.04)
for _x in (16.4,17.2,18,18.8,19.6):
    planter(_x,19.7,6.5,.43+(_x%1)*.15)
for _x in (16.6,19.4):
    pm_arch('Botanica greenhouse brass rib',_x,19.5,6.55,1.3,7.5,.65,M['Gold'],.024)
    for _yy in (19.3,19.8):cube('Botanica glazed terrarium base',(_x,_yy,6.56),(1.2,.35,.07),M['Green'],.02)
pm_tag_since(_b,'Botanica greenhouse window',(18,19.6,5.81))
coll('Botanica stepped plant display',(18,19.6,6.5),(4.6,1.7,1.4))

# The upper front corners become furnished destination lounges. The inner
# gallery edge x=14..16.3 stays clear; all furniture is beyond that strip.
for _sign,_x,_color,_title in [(-1,-19.5,'Teal','THE ORANGE GROVE'),(1,19.5,'Candy','CLOUD NINE LOUNGE')]:
    GROUP='Upper gallery café lounges'
    cube('Upper lounge '+_title+' feature wall',(_x,-10.5,8.0),(7.4,.16,4.2),M[_color],.08)
    cube('Upper lounge warm cornice',(_x,-10.7,10.2),(7.6,.6,.15),M['Gold'],.04)
    text(_title,(_x,-10.62,9.6),.42,M['SignWhite'],extrude=.015)
    text('RELAX • REFRESH • RECHARGE',(_x,-10.64,9.18),.17,M['Cream'])
    cube('Upper lounge pearl inset floor',(_x,-15.1,5.825),(7.0,7.8,.025),M['GalleryIvory'],.07)
    for _k,_y in enumerate((-13.1,-17.0)):
        pm_table(_x,_y,color=_color,unit=str((_sign,_k)))
    # Built-in banquette along outer wall with plump cushions and ribbed base.
    _b=set(scene.objects)
    _bx=_x+_sign*2.63
    cube('Upper lounge banquette plinth',(_bx,-15.2,6.05),(1.0,6.5,.48),M['GalleryWalnut'],.12)
    cube('Upper lounge plush seat',(_bx,-15.2,6.34),(1.0,6.5,.21),M[_color],.1)
    cube('Upper lounge tufted back',(_bx+_sign*.39,-15.2,6.81),(.22,6.5,1.0),M[_color],.1)
    for _i in range(9):
        _y=-18.0+_i*.70
        uv('Upper lounge contrasting cushion',(_bx+_sign*.04,_y,6.68),(.22,.25,.26),M['Orange'] if _i%2 else M['GalleryRose'],20,12)
        uv('Banquette upholstered button',(_bx-_sign*.13,_y,7.03),(.024,.024,.024),M['Gold'],12,8)
    pm_tag_since(_b,'Upper lounge banquette '+str(_sign),(_bx,-15.2,5.81))
    coll('Upper lounge banquette',(_bx,-15.2,6.45),(1.2,6.7,1.3))
    for _y in (-12.0,-15.0,-18.5):
        pm_pendant(_x,_y,12.4,9.0,'Orange' if _sign<0 else 'GalleryRose',.48)
    for _y in (-11.5,-19):
        _b=set(scene.objects);planter(_x-_sign*2.7,_y,5.81,.72)
        pm_tag_since(_b,'Upper lounge planter '+str((_sign,_y)),(_x-_sign*2.7,_y,5.81))
    light('Upper lounge '+_title+' warm pool',(_x,-15,10.8),'FFE1B3',650,5,unity_intensity=1.4,ran=8)

# Continuous architectural fascia, embossed sun medallions and botanical
# balconies make the second story read as a designed retail promenade.
GROUP='Premium mezzanine balustrades'
for _sign in (-1,1):
    _x=_sign*14.03
    cube('Promenade deep enamel fascia',(_x,-3.5,5.46),(.20,36.9,.56),M['Orange'],.035)
    for _z in (5.20,5.73):cube('Promenade brass continuous reveal',(_x-_sign*.12,-3.5,_z),(.025,36.9,.026),M['Gold'])
    for _y in range(-20,15,2):
        # High-quality repeated detailing reads down the full perspective.
        cube('Promenade baluster ivory inset',(_x,_y,6.31),(.16,.16,1.03),M['GalleryIvory'],.025)
        cyl('Promenade post finial',(_x,_y,6.87),.11,.07,M['Gold'],24)
        for _dy in (-.68,.68):
            rod('Promenade ornamental diagonal',(_x,_y+_dy,5.92),(_x,_y,6.7),.018,M['Gold'])
    for _y in (-17,-9,-1,7,13):
        _b=set(scene.objects)
        _plate=cyl('Promenade sun medallion',(_x-_sign*.14,_y,5.45),.21,.045,M['Gold'],32);_plate.rotation_euler[1]=math.pi/2
        uv('Promenade sun enamel center',(_x-_sign*.17,_y,5.45),(.029,.13,.13),M['Cream'],24,16)
        pm_tag_since(_b,'Promenade medallion '+str((_sign,_y)),(_x,_y,5.45))
for _x in (-12,-8,-4,0,4,8):
    # Rear railing stops before the existing twin escalator arrival.
    cube('Rear gallery baluster ivory inset',(_x,15.02,6.31),(.16,.16,1.03),M['GalleryIvory'],.025)
    for _dx in (-.72,.72):rod('Rear gallery ornamental diagonal',(_x+_dx,15.02,5.92),(_x,15.02,6.7),.018,M['Gold'])
cube('Rear gallery enamel fascia',(-3,15.03,5.46),(22,.2,.56),M['Orange'],.035)
cube('Rear gallery gold reveal',(-3,14.91,5.22),(22,.025,.028),M['Gold'])

# Kitchen: copper cookware, tiled feature graphic, prep ingredients and open
# crockery shelves. These are static scenery dressing for the existing kitchen.
GROUP='Premium kitchen studio dressing'
for _x in (-21.55,-20.2,-18.85,-17.5,-16.15):
    for _z in (7.35,7.8,8.25):
        cube('Kitchen backsplash hand glazed tile',(_x,2.19,_z),(1.26,.018,.40),M['Teal'] if int(_x*10)%2 else M['GalleryTurquoise'],.022)
for _x in (-21.6,-20.8,-18.8,-18.0):
    _b=set(scene.objects)
    for _i in range(5):cyl('Kitchen crockery plate stack',(_x,1.50,7.38+_i*.027),.23,.03,M['Cream'],32)
    pm_tag_since(_b,'Kitchen crockery '+str(_x),(_x,1.5,7.38))
_b=set(scene.objects)
cube('Kitchen chopping board',(-17,-1.5,7.245),(.63,.51,.055),M['Oak'],.025)
for _j in range(5):food(['carrot','tomato','broccoli'][_j%3],(-17.22+_j*.1,-1.55+(_j%2)*.15,7.28),.23)
cyl('Kitchen copper stockpot',(-20,-1.9,7.43),.24,.40,M['Gold'],32)
torus('Kitchen stockpot rolled lip',(-20,-1.9,7.64),.24,.016,M['Chrome'])
for _dx in (-.31,.31):
    _o=torus('Kitchen stockpot handle',(-20+_dx,-1.9,7.5),.078,.019,M['Gold']);_o.rotation_euler[0]=math.pi/2
pm_tag_since(_b,'Kitchen live preparation art',(-19,-1.5,7.21))
for _x in (-21,-19,-17):pm_pendant(_x,-1.5,11.7,9.3,'Orange',.32)

# Gym: two sculpted stationary cycles and organized yoga/storage dressing.
# No scripts, animation, input handling or mechanics are attached.
GROUP='Premium gym studio dressing'
for _idx,_x in enumerate((17.9,20.7)):
    _y=-6.3;_z=5.81;_b=set(scene.objects)
    cube('Gym cycle protective mat',(_x,_y,_z+.021),(1.2,2.2,.045),M['Blue'],.1)
    for _dy in (-.73,.73):
        rod('Gym cycle chrome stabilizer',(_x-.5,_y+_dy,_z+.14),(_x+.5,_y+_dy,_z+.14),.065,M['Chrome'])
    for _side in (-1,1):
        rod('Gym cycle sculpted frame',(_x+_side*.24,_y-.73,_z+.22),(_x+_side*.15,_y+.4,_z+.89),.065,M['Orange'])
        rod('Gym cycle frame return',(_x+_side*.15,_y+.4,_z+.89),(_x+_side*.24,_y+.73,_z+.22),.055,M['Teal'])
    _o=cyl('Gym cycle flywheel',(_x,_y+.39,_z+.54),.35,.18,M['Navy'],48);_o.rotation_euler[1]=math.pi/2
    for _side in (-1,1):
        _o=torus('Gym cycle flywheel orange rim',(_x+_side*.102,_y+.39,_z+.54),.285,.027,M['Orange']);_o.rotation_euler[1]=math.pi/2
    rod('Gym cycle adjustable saddle stem',(_x,_y-.37,_z+.29),(_x,_y-.28,_z+1.08),.045,M['Chrome'])
    cube('Gym cycle soft ergonomic saddle',(_x,_y-.28,_z+1.10),(.44,.51,.12),M['Navy'],.07)
    rod('Gym cycle handlebar stem',(_x,_y+.55,_z+.55),(_x,_y+.59,_z+1.30),.046,M['Chrome'])
    for _side in (-1,1):
        rod('Gym cycle foam hand grip',(_x,_y+.59,_z+1.30),(_x+_side*.39,_y+.45,_z+1.39),.043,M['Black'])
    cube('Gym cycle cyan studio display',(_x,_y+.61,_z+1.33),(.30,.18,.06),M['Ice'],.027)
    pm_tag_since(_b,'Gym cycle '+str(_idx),(_x,_y,_z))
    coll('Static gym cycle',(_x,_y,_z+.72),(1.2,2.2,1.45))
_b=set(scene.objects)
cube('Gym open storage bench',(22.5,-5.8,6.36),(1.0,4.8,1.1),M['GalleryLavender'],.08)
for _i in range(7):
    _y=-7.7+_i*.6
    _o=cyl('Gym neatly rolled yoga mat',(22.35,_y,7.05),.15,.65,M[['Candy','Teal','Orange'][_i%3]],24);_o.rotation_euler[0]=math.pi/2
    torus('Gym yoga mat top binding',(22.35,_y,7.05),.10,.012,M['Cream'])
pm_tag_since(_b,'Gym yoga storage',(22.5,-5.8,5.81))
coll('Gym storage bench',(22.5,-5.8,6.4),(1.1,4.9,1.2))
for _x in (17.5,20.5):pm_pendant(_x,-5.8,11.8,9.4,'GalleryLavender',.35)

print('Premium mezzanine: five dimensional boutiques, two furnished lounges, dressed kitchen and gym.',flush=True)
