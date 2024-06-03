#version 100
precision highp float;

uniform mat4 uModel;
uniform mat4 uView;
uniform mat4 uProjection;

attribute vec4 p3d_Color;

varying vec4 color;

attribute vec4 p3d_Vertex;
uniform mat4 p3d_ModelViewProjectionMatrix;
varying vec3 pos;

void main() {
    //gl_Position = uProjection * uView * uModel * p3d_ModelViewProjectionMatrix * p3d_Vertex;
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    color = p3d_Color;
    pos = p3d_Vertex.xyz;
}


__split__


#version 100
precision highp float;


varying vec4 color;

void main() {
    gl_FragColor = color;
}
