#!/usr/bin/env node
import fs from "fs";
import path from "path";
import child_process from "child_process";

const projectName = process.argv[2];

if (projectName == null || projectName.length == 0) {
    console.error("Project name is required. Usage: npx create-django-app <project_name>");
    process.exit(1);
}

const cleanup = () => {
    console.log("Cleaning up.");
};

const handleExit = () => {
    cleanup();
    console.log("Exiting without error.");
    process.exit();
};

const handleError = (e: unknown) => {
    console.error("ERROR! An error was encountered while executing");
    console.error(e);
    cleanup();
    console.log("Exiting with error.");
    process.exit(1);
};

process.on("SIGINT", handleExit);
process.on("uncaughtException", handleError);

try {
    const nixStatus = child_process.execSync(`nix --version`, {stdio: "ignore"});
} catch (error) {
    console.log(
        "You need to install nix. Visit https://nixos.org/download.html to get started",
    );
    throw error;
}

child_process.execSync(`${__dirname}/scripts/create-django-app.sh ${projectName}`, {stdio: "inherit"});
