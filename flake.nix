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
                python310Packages.poetry
                python310Packages.django
            ];
        };

        packages.gtf_order_api= with pkgs.poetry2nix; mkPoetryApplication {
            projectDir = ./ordering-system;
            preferWheels = true;
        };

        apps.gtf_order_api = utils.lib.mkApp {
            drv = self.packages.gtf_order_api."${system}";
        };

    }; in with utils.lib; eachSystem defaultSystems out;

}
