#version 120

uniform mat4 p3d_ProjectionMatrix;
uniform mat4 p3d_ViewMatrix;

attribute vec4 p3d_Vertex;

varying vec3 v_texcoord;

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
////attribute vec2 aUV;
//attribute vec2 p3d_MultiTexCoord0;
//
//varying vec2 uv;
//
//attribute vec4 p3d_Vertex;
//uniform mat4 p3d_ModelViewProjectionMatrix;
//
//void main() {
//    //gl_Position = uProjection * uView * uModel * p3d_ModelViewProjectionMatrix * p3d_Vertex;
//    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
//    //uv = aUV;
//    uv = p3d_MultiTexCoord0;
//}


__split__

#version 120

#ifdef USE_330
    #define textureCube texture

    out vec4 o_color;
#endif

uniform samplerCube skybox;

varying vec3 v_texcoord;

void main() {
    vec4 color = textureCube(skybox, v_texcoord);
#ifdef USE_330
    o_color = color;
#else
    gl_FragColor = color;
#endif
}


//#version 100
//precision highp float;
//
//uniform sampler2D uTexture;
//
//varying vec2 uv;
//
//void main() {
//    gl_FragColor = texture2D(uTexture, uv);
//
//}
