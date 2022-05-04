{
    inputs = {
        nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
        utils.url = "github:numtide/flake-utils";
    };

    outputs = {self, nixpkgs, utils}:
    let out = system:
    let pkgs = nixpkgs.legacyPackages."${system}";
    in {

        devShell = pkgs.mkShell {
            buildInputs = with pkgs; [
                monero-cli
                python310Packages.poetry
                python310Packages.django
            ];
        };

        packages = {
            ordering-api = pkgs.poetry2nix.mkPoetryApplication {
                projectDir = ./ordering-api;
                preferWheels = true;
            };
            create-address-service = pkgs.poetry2nix.mkPoetryApplication {
                projectDir = ./create-address-service;
                preferWheels = true;
            };
        };

        apps = {
            ordering-api = utils.lib.mkApp {
                drv = self.packages.ordering-api."${system}";
            };
            create-address-service = pkgs.poetry2nix.mkPoetryApplication {
                projectDir = ./create-address-service;
                preferWheels = true;
            };
        };

    }; in with utils.lib; eachSystem defaultSystems out;

}
