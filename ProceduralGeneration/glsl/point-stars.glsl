#version 150
precision highp float;

uniform mat4 uModel;
uniform mat4 uView;
uniform mat4 uProjection;

in vec4 p3d_Color;

out vec4 pColor;

in vec4 p3d_Vertex;
uniform mat4 p3d_ModelViewProjectionMatrix;
out vec3 pos;

void main() {
    //gl_Position = uProjection * uView * uModel * p3d_ModelViewProjectionMatrix * p3d_Vertex;
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    pColor = p3d_Color;
    pos = p3d_Vertex.xyz;
}


__split__


#version 150
precision highp float;


in vec4 pColor;
out vec4 color;

void main() {
    color = pColor;
}
