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

uniform bool MakeBrightStars;
uniform bool MakePointStars;

uniform int BrightStar_Size;
uniform int PointStar_Size;

uniform sampler2D BrightStar_Data;
uniform sampler2D PointStar_Data;

uniform int Nebula_Count;
uniform int Nebula_Steps;
uniform vec3 Nebula_Color[6];
uniform vec3 Nebula_Offset[6];
uniform float Nebula_Intensity[6];
uniform float Nebula_Falloff[6];

uniform bool NebulaPrecomputed;
uniform sampler3D NebulaNoise3D;

//uniform float osg_FrameTime;

in vec3 pos;
out vec4 color;

__noise4d__

float noise_n(vec3 p) { return 0.5 * cnoise(vec4(p, 0)) + 0.5; }

__util__

//////////////////////////////////////////////////////////

vec3 star(vec2 p2, vec3 p) {
    float blinkIntensity = 0.15;
    int starMult = 29-PointStar_Size;
    float xFact = 1;
    float yFact = 30;
    xFact *= starMult;
    yFact *= starMult;
    
    vec3 ps = cartesianToSpherical(p);
    float theta = abs(0.5-abs((floor(ps.y*yFact)/yFact-pi/2)/pi));
    float tf = floor(theta*900)/90+1;
    
    //vec3 pd = vec3(fract(ps.xy*2),ps.z);
    if(theta<0.004){
        tf = floor(theta*80)/8+0.45;
    } else if(theta<0.008){
        tf = floor(theta*80)/8+0.6;
    } else if(theta<0.02){
        tf = floor(theta*80)/8+0.8;
    }
    
    ps.x += 0.5*(mod((floor(ps.y*yFact))+80,2));
    
    float TheX = ps.x*xFact*pow(tf,2);
    float TheY = abs(ps.y*yFact);
    
    vec3 pc = sphericalToCartesian(vec3(abs(fract(TheX)), abs(fract(TheY)), ps.z));
    float d = length(pc.xy-vec2(0.5,0.5));
    vec3 cords = sphericalToCartesian(vec3(floor(TheX), floor(TheY), 1));
    
    float starIntensity = smoothstep(4.4/yFact*starMult, 3.8/yFact*starMult, d);
    
    //starIntensity *= maxComponent(texture2D(PointStar_Data, vec2(floor(TheX),floor(TheY))));
    //starIntensity *= maxComponent(texture2D(PointStar_Data, vec2(floor(ps.x)+floor(ps.y),0)));
    if(texture2D(PointStar_Data, cords.xy) == vec4(0)) return vec3(0,0,0);
    
    return starIntensity * (1-(texture2D(PointStar_Data, cords.xy).rgb)*0.25);
    //return starIntensity * (1-(texture2D(PointStar_Data, cords.xy).rgb)*0.25) * (1 - blinkIntensity/2 + sin(osg_FrameTime*2+(mod(floor(noise_n(cords)*80),20)))*(blinkIntensity/2) );
    //return vec3(starIntensity);
}

vec4 star_bright(vec2 p2, vec3 p) {
    float blinkIntensity = 0.25;
    int starMult = 29-BrightStar_Size;
    float xFact = 1;
    float yFact = 30;
    xFact *= starMult;
    yFact *= starMult;
    
    vec3 ps = cartesianToSpherical(p);
    float theta = abs(0.5-abs((floor(ps.y*yFact)/yFact-pi/2)/pi));
    float tf = floor(theta*900)/90+1;
    
    //vec3 pd = vec3(fract(ps.xy*2),ps.z);
    if(theta<0.004){
        tf = floor(theta*80)/8+0.45;
    } else if(theta<0.008){
        tf = floor(theta*80)/8+0.6;
    } else if(theta<0.02){
        tf = floor(theta*80)/8+0.8;
    }
    
    ps.x += 0.5*(mod((floor(ps.y*yFact))+80,2));
    
    float TheX = ps.x*xFact*pow(tf,2);
    float TheY = abs(ps.y*yFact);
    
    vec3 pc = sphericalToCartesian(vec3(abs(fract(TheX)), abs(fract(TheY)), ps.z));
    float d = length(pc.xy-vec2(0.5,0.5));
    vec3 cords = sphericalToCartesian(vec3(floor(TheX), floor(TheY), 1));
    
    float starIntensity = smoothstep(4.4/yFact*starMult*0.9, 3.8/yFact*starMult*0.2, d);
    
    //starIntensity *= maxComponent(texture2D(BrightStar_Data, vec2(floor(TheX),floor(TheY))));
    //starIntensity *= maxComponent(texture2D(BrightStar_Data, vec2(floor(ps.x)+floor(ps.y),0)));
    
    vec3 c = vec3(0);
    
    if(starIntensity < 0.1 || texture2D(BrightStar_Data, cords.xy) == vec4(0)){
        starIntensity = 0;
    }else if(starIntensity < 0.8){
        c = texture2D(BrightStar_Data, cords.xy).rgb;
    }else{
        c = texture2D(BrightStar_Data, cords.xy).rgb;
        if(c.r >= c.g){
            if(c.r >= c.b) c.r = 1.0;
            else           c.b = 1.0;
        }else{
            if(c.g >= c.b) c.g = 1.0;
            else           c.b = 1.0;
        }
    }
    
    return vec4(c, starIntensity);
    //return vec4(c * ( 1 - blinkIntensity/2 + sin(osg_FrameTime*2+(mod(floor(noise_n(cords)*80),20)))*(blinkIntensity/2) ) , starIntensity);
}

//////////////////////////////////////////////////////////

float drawCircle(vec3 pos, vec3 circlePos, float circleRadius) { //NOTE: Unused but will be useful for the sun drawing function
    vec3 circleCenter = sphericalToCartesian(circlePos);
    float d = length(pos - circleCenter);
    float circle = 1.0 - smoothstep(circleRadius*0.199, circleRadius*1.1, d);
    return circle;
}

float nebula(vec3 p, const int steps) {
    // Nebula from https://github.com/wwwtyro/space-3d under the unlicense license
    float scale = pow(2.0, float(steps));
    vec3 displace = vec3(0);
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
void main_g() {
    vec3 view_dir = normalize(pos);
    vec2 skybox_uv;
    skybox_uv.x = (atan(view_dir.y, view_dir.x) + (0.5 * pi)) / (2.0 * pi);
    skybox_uv.y = clamp(view_dir.z * 0.72 + 0.35, 0.0, 1.0);
    
    vec4 colour = vec4(0.0, 0.0, 0.0, 0.0);
    
    // --- Nebula Computation ---
    vec3 nebulaEffect = vec3(0.0);
    if (NebulaPrecomputed) {
        if (Nebula_Count > 0) {
            vec3 noiseCoordBase = (view_dir + vec3(1.0)) * 0.5;
            for (int i = 0; i < Nebula_Count; i++) {
                float sampleAccum = 0.0;
                for (int s = 0; s < Nebula_Steps; s++) {
                    float stepFactor = (Nebula_Steps > 1) ? float(s) / float(Nebula_Steps - 5) : 0.0;
                    vec3 noiseCoord = noiseCoordBase + Nebula_Offset[i] * stepFactor;
                    sampleAccum += texture(NebulaNoise3D, noiseCoord).r;
                }
                float noiseValue = sampleAccum / float(Nebula_Steps);
                
                // Adjust thresholds here if necessary.
                float mask = smoothstep(0.55, 0.75, noiseValue) * Nebula_Intensity[i];
                float falloff = smoothstep(0.0, 1.0, dot(view_dir, vec3(0.0, 0.3, 0.0))) * Nebula_Falloff[i];
                nebulaEffect += Nebula_Color[i] * mask * falloff;
                
                float c = min(1.0, mask);
                c = pow(c, Nebula_Falloff[i]);
                colour = mixInNebulaColor(colour, vec4(Nebula_Color[i] * mask * falloff, c));
            }
            //colour.rgb += nebulaEffect;
        }
    } else {
        for (int i = 0; i < Nebula_Count; i++) {
            float c = min(1.0, nebula(view_dir + Nebula_Offset[i], Nebula_Steps) * Nebula_Intensity[i]);
            c = pow(c, Nebula_Falloff[i]);
            c = min(c, 1.0);
            colour = mixInNebulaColor(colour, vec4(Nebula_Color[i], c));
        }
    }
    
    // --- Star Contributions ---
    if (MakePointStars) {
        vec3 starIntensity = star(skybox_uv, view_dir);
        colour.rgb += starIntensity;
        colour.a = max(colour.a, maxComponent(starIntensity));
    }
    
    if (MakeBrightStars) {
        vec4 starIntensity = star_bright(skybox_uv, view_dir);
        colour.rgb += starIntensity.rgb;
        colour.a = max(colour.a, starIntensity.a);
    }
    
    // Instead of using alpha from 'colour' directly, use a fixed mix factor.
    // For example, use mixFactor = 0.5 (or compute one based on the nebula contribution).
    float mixFactor = 0.5;
    color = vec4(mix(bgColor.rgb, colour.rgb, mixFactor), 1.0);
}

void main() {
    vec3 view_dir = normalize(pos);
    vec2 skybox_uv;
    // Convert spherical coordinates
    skybox_uv.x = (atan(view_dir.y, view_dir.x) + (0.5 * pi)) / (2 * pi);
    skybox_uv.y = clamp(view_dir.z * 0.72 + 0.35, 0.0, 1.0);
    
    vec4 colour = vec4(0,0,0,0);
    
    // Add Nebulae
    float c = 0.0;
    if(NebulaPrecomputed){
        if (Nebula_Count > 0) {
            // Nebula effect accumulation.
            vec3 nebulaEffect = vec3(0.0);
            // Map the direction from [-1, 1] to [0, 1] to get base coordinates for noise sampling.
            vec3 noiseCoordBase = (view_dir + vec3(1.0)) * 0.5;
            for (int i = 0; i < Nebula_Count; i++) {
                float sampleAccum = 0.0;
                
                
                for (int s = 0; s < Nebula_Steps; s++) {
                    float stepFactor = (Nebula_Steps > 1) ? float(s) / float(Nebula_Steps - 5) : 0.0;
                    vec3 noiseCoord = noiseCoordBase;// + Nebula_Offset[i] * stepFactor;
                    sampleAccum += texture(NebulaNoise3D, noiseCoord).r / float(Nebula_Steps);
                }
                
                //int s = 0;
                //vec3 noiseCoord = noiseCoordBase + Nebula_Offset[i];
                //sampleAccum += texture(NebulaNoise3D, noiseCoord).r;
                
                
                float noiseValue = sampleAccum;
                // Adjust thresholds here if necessary.
                float mask = smoothstep(0.55, 0.65, noiseValue) * Nebula_Intensity[i];
                float falloff = 1;//smoothstep(0.0, 1.0, dot(view_dir, vec3(0.0, Nebula_Intensity[i]/3, 0.0))) * Nebula_Falloff[i];
                //float falloff = smoothstep(0.5, 1.0, (dot(view_dir, vec3(0.0, Nebula_Intensity[i]/2, 0.0)) + 1.0) * 0.5) * Nebula_Falloff[i];
                nebulaEffect += Nebula_Color[i] * mask * falloff;
                
                float c = min(1.0, mask);
                //c = pow(c, Nebula_Falloff[i]);
                colour = mixInNebulaColor(colour, vec4(Nebula_Color[i] * mask * falloff, c));
            }
            //colour.rgb += nebulaEffect;
        }
    }else{
        for(int i = 0; i<Nebula_Count; i++){
            c = min(1.0, nebula(view_dir + Nebula_Offset[i], Nebula_Steps) * Nebula_Intensity[i]);
            c = pow(c, Nebula_Falloff[i]);
            colour = mixInNebulaColor(colour, vec4(Nebula_Color[i], c));
        }
    }
    
    // Add Stars
    if(MakePointStars){
        vec3 starIntensity = star(skybox_uv, view_dir);
        colour.rgb += starIntensity;
        colour.a = max(colour.a, maxComponent(starIntensity));
    }
    
    // Add Bright Stars
    if(MakeBrightStars){
        vec4 starIntensity = star_bright(skybox_uv, view_dir);
        colour.rgb += starIntensity.rgb;
        colour.a = max(colour.a, starIntensity.a);
    }
    
    // Add Sun
    //if(MakeSun){
    //    //TODO: Draw Sun at location specified by python so that a lightsource can be placed there
    //}
    
    //if(colour.a == 1.0){
    //    color = colour;
    //}else{
    //    color = vec4(colour.rgb + bgColor.rgb, 1.0);
    //}
    
    //color = vec4(colour.rgb*colour.a + bgColor.rgb*(1.0-colour.a), 1.0);
    
    float mixFactor = 0.5;
    color = vec4(mix(bgColor.rgb, colour.rgb, mixFactor), 1.0);
}
