#version 150
precision highp float;

in vec4 p3d_Vertex;
uniform mat4 p3d_ModelViewProjectionMatrix;
out vec3 pos;

void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    pos = p3d_Vertex.xyz;
}


__split__


#version 150
precision highp float;
precision highp int;

uniform int Seed;

uniform vec4 bgColor;

uniform bool MakeSun;

uniform int BrightStar_Count;
uniform bool MakePointStars;
uniform int Star_Count;

uniform int Nebula_Count;
uniform vec3 Nebula_Color[6];
uniform vec3 Nebula_Offset[6];
uniform float Nebula_Intensity[6];
uniform float Nebula_Falloff[6];

in vec3 pos;
out vec4 color;

__noise4d__

float noise_n(vec3 p) { return 0.5 * cnoise(vec4(p, 0)) + 0.5; }

__util__

//////////////////////////////////////////////////////////

vec3 star(vec2 p2, vec3 p) {
    vec3 ps = cartesianToSpherical(p);
    vec3 pd = vec3(fract(ps.xy*2),ps.z);
    float theta = abs(0.5-abs((ps.y-pi/2)/pi));
    float tf = floor(theta*40)/4+1;
    
    float TheX = abs(pd.x*6*pow(tf,2));
    float TheY = abs(pd.y*80);
    
    vec3 pc = sphericalToCartesian(vec3(abs(fract(TheX)), abs(fract(TheY)), pd.z));
    float d = length(pc-0.4);
    
    vec3 h = hash3(sphericalToCartesian(vec3(abs(floor(TheX)), abs(floor(TheY)), pd.z))*Seed);
    float starIntensity = smoothstep(0.0, 0.15, 0.4-d);
    
    uvec3 rpcg = pcg(vec3(floor(TheX),floor(TheY),Seed));
    
    const int steps = 16;
    float scale = pow(2.0, float(steps));
    vec3 displace;
    for (int i = 0; i < steps; i++) {
        displace = vec3(
            noise_n(p.xyz * scale + displace),
            noise_n(p.yzx * scale + displace),
            noise_n(p.zxy * scale + displace)
        );
        scale *= 0.5;
    }
    float nf = noise_n(p * scale + displace);
    
    uint Xv = getLastBits(rpcg.x + uint(nf*10000),8);
    uint Yv = getLastBits(rpcg.y + uint(nf*10000),8);
    uint Zv = getLastBits(rpcg.z + uint(nf*10000),8);
    
    if(mod(((Yv-Xv)), 7) == 0 ){
        starIntensity = 0.;
    }
    if(Xv+Yv+Zv < uint(pow(2,9)+(5-tf)*10) ){
        starIntensity = 0.;
    }
    if(uint(Xv^Yv) < uint(pow(2,7)) ){
        starIntensity = 0.;
    }
    
    return starIntensity * (1-abs(h)*0.15);
}

vec4 star_bright(vec2 p2, vec3 p) { // WIP
    vec3 ps = cartesianToSpherical(p);
    vec3 pd = vec3(fract(ps.xy*2),ps.z);
    float theta = abs(0.5-abs((ps.y-pi/2)/pi));
    float tf = floor(theta*40)/4+1;
    
    float TheX = abs(pd.x*3*pow(tf,2));
    float TheY = abs(pd.y*40);
    
    vec3 pc = sphericalToCartesian(vec3(abs(fract(TheX)), abs(fract(TheY)), pd.z));
    float d = length(pc-0.4);
    
    vec3 h = hash3(sphericalToCartesian(vec3(abs(floor(TheX)), abs(floor(TheY)), pd.z))*Seed);
    float starIntensity = smoothstep(0.0, 0.15, 0.4-d);
    
    uvec3 rpcg = pcg(vec3(floor(TheX),floor(TheY),Seed));
    
    const int steps = 16;
    float scale = pow(2.0, float(steps));
    vec3 displace;
    for (int i = 0; i < steps; i++) {
        displace = vec3(
            noise_n(rpcg.xyz * scale + displace),
            noise_n(rpcg.yzx * scale + displace),
            noise_n(rpcg.zxy * scale + displace)
        );
        scale *= 0.5;
    }
    float nf = noise_n(rpcg * scale + displace);
    
    uint Xv = getLastBits(rpcg.x + uint(nf*10000),8);
    uint Yv = getLastBits(rpcg.y + uint(nf*10000),8);
    uint Zv = getLastBits(rpcg.z + uint(nf*10000),8);
    
    if(mod(((Yv-Xv)), 7) == 0 ){
        starIntensity = 0;
    }
    if(Xv+Yv+Zv < uint(pow(2,9)+(5-tf)*10) ){
        starIntensity = 0.;
    }
    if(uint(Xv^Yv) < uint(pow(2,7)) ){
        starIntensity = 0.;
    }
    
    vec3 c = starIntensity * abs(hash3(rpcg));
    if(starIntensity < 0.1){
        starIntensity = 0;
        c = vec3(0);
    }else{
        if(maxComponent(c)==c.r)
            c.r = 1.0;
        else if(maxComponent(c)==c.g)
            c.g = 1.0;
        else
            c.b = 1.0;
    }
    return vec4(c,starIntensity);
}

//////////////////////////////////////////////////////////

// Function to draw a circle at the given spherical position
float drawCircle(vec3 pos, vec3 circlePos, float circleRadius) {
    // Convert spherical coordinates to Cartesian coordinates
    vec3 circleCenter = sphericalToCartesian(circlePos);
    
    // Calculate the distance from the current position to the center of the circle
    float d = length(pos - circleCenter);
    
    // Use smoothstep to create a smooth edge for the circle
    float circle = 1.0 - smoothstep(circleRadius*0.199, circleRadius*1.1, d);
    
    return circle;
}

vec4 brightStars(vec2 p2, vec3 p, int starCount) {
    //TODO: I think it would be best to generate these random numbers in python. Or alternatively implement a good rng in lgsl;
    // The current positions are not quite uniformly distributed enough
    float starIntensity = 0.0;
    vec3 rp;
    if(bool(1)){
        for (int i = 0; i < starCount; i++) {
            rp = randPosS(p2, vec3(i+7,(i+10),2*i+28), cartesianToSpherical(p).z, Seed);
            starIntensity = drawCircle(p, rp, 0.001);
            if(starIntensity > 0.1) break;
        }
    } else {
        starIntensity = drawCircle(p, sphericalToCartesian(vec3(0.5,0.5,cartesianToSpherical(p).z)), 0.12);
    }
    
    vec3 c = vec3(0);
    if(starIntensity < 0.1){
        starIntensity = 0;
    }else{
        c = starIntensity * abs(hash3(rp));
        if(maxComponent(c)==c.r)
            c.r = 1.0;
        else if(maxComponent(c)==c.g)
            c.g = 1.0;
        else
            c.b = 1.0;
    }
    
    return vec4(c,starIntensity);
}

float nebula(vec3 p) {
    // Nebula from https://github.com/wwwtyro/space-3d under the unlicense license
    const int steps = 6;
    float scale = pow(2.0, float(steps));
    vec3 displace;
    for (int i = 0; i < steps; i++) {
        displace = vec3(
            noise_n(p.xyz * scale + displace),
            noise_n(p.yzx * scale + displace),
            noise_n(p.zxy * scale + displace)
        );
        scale *= 0.5;
    }
    return noise_n(p * scale + displace);
}

vec4 mixInNebulaColor(vec4 c1, vec4 c2){
    vec3 cn = c2.rgb * c2.w + c1.rgb * (1.0 - c2.w);
    return vec4(cn,max(c1.w,c2.w));
    //return vec4(cn,c2.w);
}
//////////////////////////////////////////////////////////////////////////////////////////////////////

void main() {
    vec3 view_dir = normalize(pos);
    vec2 skybox_uv;
    // Convert spherical coordinates
    skybox_uv.x = (atan(view_dir.y, view_dir.x) + (0.5 * pi)) / (2 * pi);
    skybox_uv.y = clamp(view_dir.z * 0.72 + 0.35, 0.0, 1.0);
    
    vec4 colour = vec4(0,0,0,0);
    
    // Add Nebulae
    float c = 0.0;
    for(int i = 0; i<Nebula_Count; i++){
        c = min(1.0, nebula(view_dir + Nebula_Offset[i]) * Nebula_Intensity[i]);
        c = pow(c, Nebula_Falloff[i]);
        colour = mixInNebulaColor(colour, vec4(Nebula_Color[i], c));
    }
    
    // Add Stars
    if(MakePointStars){
        vec3 starIntensity = star(skybox_uv, view_dir); //TODO: bring in Star_Count
        colour.rgb += starIntensity;
        colour.a = max(colour.a, maxComponent(starIntensity));
    }
    
    // Add Bright Stars
    // potentially slower version:
    vec4 starColour = brightStars(skybox_uv, view_dir, BrightStar_Count);
    colour.rgb += starColour.rgb;
    colour.a = max(colour.a, starColour.a);
    // potentially faster version but less pretty and still WIP
    //vec4 starIntensity = star_bright(skybox_uv, view_dir); //TODO: bring in BrightStar_Count
    //colour.rgb += starIntensity.rgb;
    //colour.a = max(colour.a, starIntensity.a);
    
    // Add Sun
    //if(MakeSun){
    //    //TODO: Draw Sun at location specified by python so that a lightsource can be placed there
    //}
    
    if(colour.a == 1.0){
        color = colour;
    }else{
        color = vec4(colour.rgb + bgColor.rgb, 1.0);
    }
}
