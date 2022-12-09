#vertex
#version 420

layout(location = 0) in vec3 position;

out vec2 UV;
uniform mat4 mMat;
uniform mat4 vpMat;

void main()
{
    gl_Position = vpMat * mMat * vec4(position, 1.0);
    UV = (vec2(position.x, position.y) + 1.0) / 2.0;
}


#fragment 
#version 420

layout(location = 0) out vec4 fragmentColor;
layout(binding = 0) uniform sampler2D fbImage;

in vec2 UV;

uniform float xMin;
uniform float xMax;
uniform float yMin;
uniform float yMax;
uniform float roi0;
uniform float roi1;
uniform float roi2;
uniform float roi3;

void main()
{
    fragmentColor = texture(fbImage, UV);
    vec2 px = gl_FragCoord.xy;
    if ((px.x < xMin) || (px.x > xMax) || (px.y < yMin) || (px.y > yMax))
        fragmentColor = vec4(0.0, 0.0, 0.0, 1.0);
    if ((UV.x < roi0) || (UV.x > roi2) || (UV.y < roi1) || (UV.y > roi3))
        fragmentColor.xyz *= 0.8;
}
