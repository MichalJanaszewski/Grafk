#version 330 core

struct Material {
    vec3 ambient;
    vec3 diffuse;
    vec3 specular;
    float shininess;
};

struct Light {
    vec3 position;
    vec3 ambient;
    vec3 diffuse;
    vec3 specular;
};

in vec3 FragPos;
in vec3 Normal;

uniform vec3 viewPos;
uniform Material material;
uniform Light light;

out vec4 FragColor;

float computeAttenuation(vec3 lightPos, vec3 fragPos) {
    float distance = length(lightPos - fragPos);
    return 1.0 / (1.0 + 0.09 * distance + 0.032 * distance * distance);
}

void main() {
    vec3 norm = normalize(Normal);
    vec3 lightDir = normalize(light.position - FragPos);
    vec3 viewDir = normalize(viewPos - FragPos);
    vec3 reflectDir = reflect(-lightDir, norm);

    float diff = max(dot(norm, lightDir), 0.0);
    float spec = pow(max(dot(viewDir, reflectDir), 0.0), material.shininess);

    float att = computeAttenuation(light.position, FragPos);

    vec3 ambient = light.ambient * material.ambient;
    vec3 diffuse = att * light.diffuse * diff * material.diffuse;
    vec3 specular = att * light.specular * spec * material.specular;

    FragColor = vec4(ambient + diffuse + specular, 1.0);
}
