#version 100
precision highp float;

uniform mat4 uModel;
uniform mat4 uView;
uniform mat4 uProjection;

attribute vec4 p3d_Vertex;
uniform mat4 p3d_ModelViewProjectionMatrix;
varying vec3 pos;

void main() {
    //gl_Position = uProjection * uView * uModel * p3d_ModelViewProjectionMatrix * p3d_Vertex;
    //pos = (uModel * p3d_ModelViewProjectionMatrix * p3d_Vertex).xyz;
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    pos = (p3d_ModelViewProjectionMatrix * p3d_Vertex).xyz;
    //pos = p3d_Vertex.xyz;;
}


__split__


#version 150
precision highp float;

uniform vec3 uPosition;
uniform vec3 uColor;
uniform float uSize;
uniform float uFalloff;
in vec3 pos;
out vec4 p3d_FragColor;

void main() {
    vec3 posn = normalize(pos);
    float d = 1.0 - clamp(dot(posn, normalize(uPosition)), 0.0, 1.0);
    //float d = 1.0 - clamp(posn, 0.0, 1.0);
    float i = exp(-(d - uSize) * uFalloff);
    float o = clamp(i, 0.0, 1.0);
    vec3 iv = vec3(i,i,i);
    //gl_FragColor  = vec4(uColor + iv, o);
    p3d_FragColor = vec4(uColor + iv, o);
}
