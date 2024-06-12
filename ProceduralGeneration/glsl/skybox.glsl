#version 150

uniform mat4 p3d_ProjectionMatrix;
uniform mat4 p3d_ViewMatrix;

in vec4 p3d_Vertex;

out vec3 v_texcoord;

void main() {
    v_texcoord = p3d_Vertex.xyz;
    mat4 view = mat4(mat3(p3d_ViewMatrix));
    gl_Position = p3d_ProjectionMatrix * view * p3d_Vertex;
}

//#version 100
//precision highp float;
//
//uniform mat4 uModel;
//uniform mat4 uView;
//uniform mat4 uProjection;
//
////in vec2 aUV;
//in vec2 p3d_MultiTexCoord0;
//
//out vec2 uv;
//
//in vec4 p3d_Vertex;
//uniform mat4 p3d_ModelViewProjectionMatrix;
//
//void main() {
//    //gl_Position = uProjection * uView * uModel * p3d_ModelViewProjectionMatrix * p3d_Vertex;
//    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
//    //uv = aUV;
//    uv = p3d_MultiTexCoord0;
//}


__split__

#version 150
#extension GL_NV_shadow_samplers_cube : enable

out vec4 color;

uniform samplerCube skybox;

in vec3 v_texcoord;

void main() {
    color = textureCube(skybox, v_texcoord);
}


//#version 100
//precision highp float;
//
//uniform sampler2D uTexture;
//
//out vec2 uv;
//
//void main() {
//    gl_FragColor = texture2D(uTexture, uv);
//
//}
