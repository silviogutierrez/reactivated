export default {
    "presets": [
        ["@babel/preset-typescript", {"allowNamespaces": true}]
    ],
    "plugins": [
        [
            "module-resolver",
            {
                "root": ["./"],
                "alias": {
                    "@client": "./client"
                }
            }
        ]
    ]
}
