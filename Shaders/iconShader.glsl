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

layout(location=0) out vec4 fragmentColor;
layout(binding = 0) uniform sampler2D iconImage;

in vec2 UV;
in vec3 color;

void main()
{
    fragmentColor = texture(iconImage, UV);
}