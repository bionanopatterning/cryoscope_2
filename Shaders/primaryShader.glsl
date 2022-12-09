#vertex
#version 420

layout(location = 0) in vec3 position;
out vec2 UV;

void main()
{
    gl_Position = vec4(position, 1.0);
    UV = (vec2(position.x, position.y) + 1.0) / 2.0;
}

#fragment
#version 420

layout (binding = 0) uniform usampler2D channelImage;
layout (binding = 1) uniform sampler2D fbImage;

in vec2 UV;
out vec4 fragmentColor;

uniform vec3 channelColor;
uniform float contrastMin;
uniform float contrastMax;

void main()
{
    vec4 framebufferColor = texture(fbImage, UV);
    float grayScale = float(texture(channelImage, UV).r);
    float contrast = (grayScale - contrastMin) / (contrastMax - contrastMin);
    contrast = max(0.0, contrast);
    vec3 pixelColor = contrast * channelColor;
    fragmentColor = framebufferColor + vec4(pixelColor, 1.0);
    fragmentColor.a = 1.0;
}
