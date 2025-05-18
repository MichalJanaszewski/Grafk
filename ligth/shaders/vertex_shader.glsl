#version 330 core
layout(location=0) in vec3 a_position;
layout(location=1) in vec3 a_normal;

uniform mat4 model, view, projection;

out vec3 FragPos;
out vec3 Normal;

void main(){
    FragPos = vec3(model * vec4(a_position, 1.0));
    Normal = mat3(transpose(inverse(model))) * a_normal;
    gl_Position = projection * view * vec4(FragPos, 1.0);
}