import React from "react";
import Context from "reactivated/context";
import {style} from "typestyle";

import {AjaxPlayground} from "@client/generated";

export default class extends AjaxPlayground {
    static contextType = Context;

    handleOnClick = async (event: React.FormEvent<HTMLButtonElement>) => {
        const url = new URL(this.context.request.url);
        return fetch(url.toString(), {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-Requested-With": "XMLHttpRequest",
            },
            body: JSON.stringify({thing: "I am post data"}),
        })
            .then(response => response.json())
            .then(({results}) => {
                // tslint:disable-next-line
                console.log(results);
            });
    };

    handleGiveMeBackJSON = async (event: React.FormEvent<HTMLButtonElement>) => {
        const url = new URL(this.context.request.url);
        return fetch(url.toString(), {
            method: "GET",
            headers: {
                Accept: "application/json, application/xhtml+xml",
            },
        }).then(async response => {
            const parsed = await response.json();
            // tslint:disable-next-line
            console.log(response, parsed);
        });
    };

    render() {
        return (
            <div>
                <button onClick={this.handleOnClick}>Click me</button>
                <button onClick={this.handleGiveMeBackJSON}>Give me back JSON</button>
            </div>
        );
    }
}
