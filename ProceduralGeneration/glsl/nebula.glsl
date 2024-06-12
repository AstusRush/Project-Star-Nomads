#version 150
precision highp float;

uniform mat4 uModel;
uniform mat4 uView;
uniform mat4 uProjection;

in vec4 p3d_Vertex;
uniform mat4 p3d_ModelViewProjectionMatrix;
out vec3 pos;

void main() {
    //gl_Position = uProjection * uView * uModel * p3d_ModelViewProjectionMatrix * p3d_Vertex;
    //pos = (uModel * p3d_ModelViewProjectionMatrix * p3d_Vertex).xyz;
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    //pos = (p3d_ModelViewProjectionMatrix * p3d_Vertex).xyz;
    pos = p3d_Vertex.xyz;
}


__split__


#version 150
precision highp float;
precision highp int;

uniform vec3 uColor;
uniform vec3 uOffset;
uniform float uScale;
uniform float uIntensity;
uniform float uFalloff;

in vec3 pos;
//out vec4 p3d_FragColor;
out vec4 color;

__noise4d__

float noise(vec3 p) {
    return 0.5 * cnoise(vec4(p, 0)) + 0.5;
}

float nebula(vec3 p) {
    const int steps = 6;
    float scale = pow(2.0, float(steps));
    vec3 displace;
    for (int i = 0; i < steps; i++) {
        displace = vec3(
            noise(p.xyz * scale + displace),
            noise(p.yzx * scale + displace),
            noise(p.zxy * scale + displace)
        );
        scale *= 0.5;
    }
    return noise(p * scale + displace);
}

void main() {
    vec3 view_dir = normalize(pos);
    vec2 skybox_uv;
    // Convert spherical coordinates
    const float pi = 3.14159265359;
    skybox_uv.x = (atan(view_dir.y, view_dir.x) + (0.5 * pi)) / (2 * pi);
    skybox_uv.y = clamp(view_dir.z * 0.72 + 0.35, 0.0, 1.0);
    
    float c = min(1.0, nebula(view_dir + uOffset) * uIntensity);
    c = pow(c, uFalloff);
    color = vec4(uColor, c);
    //color = vec4(pos.x, pos.y/2, 0, c);
    
    
    //vec3 posn = normalize(pos) * uScale;
    //float c = min(1.0, nebula(posn + uOffset) * uIntensity);
    //c = pow(c, uFalloff);
    //p3d_FragColor = vec4(uColor, c);

}
