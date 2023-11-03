import {defineStore} from 'pinia';
import {BASE_API_URL} from "@/config/config";
import globalUtils from "@/helpers/globalUtils";

const BASE_URL = BASE_API_URL
const state = () => ({
    result: [],
    spinner: false,
    researchMinerResult: [],
    peopleMinerResult: [],
    orgMinerResult: [],
    latestProjects: [],
    customResult: [],
    personsOfTheDay: [],
    favorites: [],
    selectedDetailItem: undefined,
    stats: undefined,
    relatedEntities: [],
    graph: undefined,
    fetchedNode: undefined,
    relatedNodes: []
})

const getters = {
    getResult: (state) => {
        let result = Array.from(new Map(state.result.map(obj => [obj._id, obj])).values())
        result.sort(function (a, b){
            return b._score - a._score
        })
        return result
    },
    getLatestProjects:  (state) => {
        let result = state.latestProjects
        result.sort(function (a, b){
            return b._source.last_update.localeCompare(a._source.last_update)
        })
        return result.slice(0, 6)
    },
    getSelectedDetailItem: (state) => state.selectedDetailItem,
    getCustomResult: (state) => {
        let result = Array.from(new Map(state.customResult.map(obj => [obj._id, obj])).values())
        result.sort(function (a, b){
            return b._score - a._score
        })
        return result
    },
    getRelatedEntities: (state) => {
        let result = Array.from(new Map(state.relatedEntities.map(obj => [obj._id, obj])).values())
        result.sort(function (a, b){
            return b._score - a._score
        })
        return result
    },
    getPersonsOfTheDay: (state) => state.personsOfTheDay,
    getStats: (state) => state.stats,
    isSpinning: (state) => state.spinner,
    getGraph: (state) => state.graph,
    getFetchedNode: (state) => state.fetchedNode,
    getRelatedNodes: (state) => state.relatedNodes,
}

const actions = {
    resetResult(){
      this.result = []
    },
    resetLatestProjects(){
        this.latestProjects = []
    },
    resetCustomResult(){
        this.customResult = []
    },
    resetStats() {
        this.stats = {}
    },
    resetPersonsOfTheDay() {
        this.personsOfTheDay = []
    },
    resetRelatedEntities() {
        this.relatedEntities = []
    },
    resetRelatedNodes(){
      this.relatedNodes = []
    },
    addRecentlyViewedItem(item){
        let recentlyViewed = JSON.parse(localStorage.getItem("recently_viewed"))
        if(recentlyViewed === null)
            recentlyViewed = []

        const isElementAlreadyInArray = recentlyViewed.some((element) => {
            return (
                element._id === item._id
            )
        })

        if (!isElementAlreadyInArray)
            recentlyViewed.unshift(item);

        if (recentlyViewed.length > 6)
            recentlyViewed.pop();

        localStorage.setItem("recently_viewed", JSON.stringify(recentlyViewed))
    },
    addFavorite(item){
        let favorites = JSON.parse(localStorage.getItem("favorites"))

        if(favorites === null)
            favorites = []

        const isElementAlreadyInArray = favorites.some((element) => {
            return (
                element._id === item._id
            )
        })

        if (!isElementAlreadyInArray)
            favorites.push(item);

        localStorage.setItem("favorites", JSON.stringify(favorites))
    },
    removeFavorite(item){
        let favorites = JSON.parse(localStorage.getItem("favorites"))
        favorites = favorites.filter(obj => obj._id !== item._id)
        localStorage.setItem("favorites", JSON.stringify(favorites))
    },
    isFavorite(item){
        let favorites = JSON.parse(localStorage.getItem("favorites"))
        if(favorites === null)
            favorites = []

        return favorites.some((element) => {
            return (
                element._id === item._id
            )
        })
    },
    createChildNode(item){
        let label = ""
        let link = `/detail/${item._index}/${item._id}`
        let shortType = ""
        let entityType = globalUtils.extractTypeFromIndex(item._index)

        if(entityType === "research project"){
            label = item._source.title
            shortType = "research_project"
        }

        else if (entityType === "people"){
            label = item._source.name
            shortType = "people"
        }

        else if (entityType === "organization"){
            label = item._source.name
            shortType = item._source.type
        }

        return {
            label: label,
            some_id: item._id,
            index: item._index,
            link: link,
            type : globalUtils.extractTypeFromDocument(shortType),
            children: [],
            expand: false
        }
    },
    addChildNode(graph, parentId, nodesToAdd) {
        const parentNode = findNodeById(graph, parentId);
        if (parentNode) {
            nodesToAdd.forEach( node => {
                if(!findNodeById(graph, node.some_id))
                    parentNode.children.push(node);
            })
        } else {
            console.error('Parent node not found.');
        }
        function findNodeById(node, id) {
            if (node.some_id === id) {
                return node;
            } else if (node.children) {
                for (const childNode of node.children) {
                    const foundNode = findNodeById(childNode, id);
                    if (foundNode) {
                        return foundNode;
                    }
                }
            }
            return null;
        }

        this.spinner = false
    },
    createNodes(root, related){
        related = related.filter( ( item => {
            return item._id !== root._id
        }))

        let nodes = []
        globalUtils.extractTopXByType(related, "people", 5).forEach(item => {
            nodes.push(item)
        })
        globalUtils.extractTopXByType(related, "research project", 5).forEach(item => {
            nodes.push(item)
        })
        globalUtils.extractTopXByType(related, "organization", 5).forEach(item => {
            nodes.push(item)
        })

        let label = ""
        let link = `/detail/${root._index}/${root._id}`
        let entityType = globalUtils.extractTypeFromIndex(root._index)
        let shortType = ""

        if(entityType === "research project"){
            label = root._source.title
            shortType = "research_project"
        }

        else if (entityType === "people"){
            label = root._source.name
            shortType = "people"
        }

        let graph = {
            label: label,
            expand: true,
            some_id: root._id,
            index: root._index,
            link: link,
            type : globalUtils.extractTypeFromDocument(shortType),
            children: [],
        }

        nodes.forEach( item => {
            graph.children.push(this.createChildNode(item))
        })
        this.graph = graph
    },
    async fetchResearchMinerDocuments(param) {
        this.spinner = true

        const query = {
            query: {
                bool: {
                    should: [
                        {
                            match: {
                                content: {
                                    query: param.searchField.toLowerCase(),
                                    boost: 2.0
                                }
                            }
                        },
                        {
                            regexp: {
                                content: {
                                    value: `.*${param.searchField.toLowerCase()}.*`,
                                    boost: 1
                                }
                            }
                        }
                    ]
                },
            },
            size: 20,
            _source: ["title", "id", "type", "last_update", "url", "lang"],
            sort: [
                {
                    _score: {
                        order: "desc"
                    }
                }
            ]
        }

        try {
            const response = await fetch(BASE_URL + param.endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(query)
            })

            this.researchMinerResult = await response.json()
            this.result.push(...this.researchMinerResult.hits.hits)

            this.spinner = false

        } catch (error) {
            console.log(error)
            this.spinner = false
        }
    },
    async fetchPeopleMinerDocuments(param) {
        this.spinner = true

        const query = {
            query: {
                bool: {
                    should: [
                        {
                            match: {
                                name: {
                                    query: param.searchField.toLowerCase(),
                                    boost: 10
                                }
                            }
                        },
                        {
                            regexp: {
                                name: {
                                    value: `.*${param.searchField.toLowerCase()}.*`,
                                    boost: 5
                                }
                            }
                        }
                    ]
                },
            },
            size: 20,
            _source: ["name", "title", "email", "homepage.url", "in.url"],
            sort: [
                {
                    _score: {
                        order: "desc"
                    }
                }
            ]
        }

        try {
            const response = await fetch(BASE_URL + param.endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(query)
            })

            this.peopleMinerResult = await response.json()
            this.result.push(...this.peopleMinerResult.hits.hits)

            this.spinner = false

        } catch (error) {
            console.log(error)
            this.spinner = false
        }
    },
    async fetchOrgMinerDocuments(param) {
        this.spinner = true

        const query = {
            query: {
                bool: {
                    should: [
                        {
                            match: {
                                name: {
                                    query: param.searchField.toLowerCase(),
                                    boost: 300
                                }
                            }
                        },
                        {
                            regexp: {
                                name: {
                                    value: `.*${param.searchField.toLowerCase()}.*`,
                                    boost: 300
                                }
                            }
                        }
                    ]
                },
            },
            size: 20,
            _source: ["link", "name", "uni", "upper", "type"],
            sort: [
                {
                    _score: {
                        order: "desc"
                    }
                }
            ]
        }

        try {
            const response = await fetch(BASE_URL + param.endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(query)
            })

            this.orgMinerResult = await response.json()
            this.result.push(...this.orgMinerResult.hits.hits)

            this.spinner = false

        } catch (error) {
            console.log(error)
            this.spinner = false
        }
    },
    async fetchLatestProjects(endpoint) {
        const query = {
            query: {
                match_all: {}
            },
            size: 6,
            _source: ["title", "id", "type", "last_update", "url", "lang"],
            sort: [
                {
                    "last_update.keyword": {
                        order: "desc"
                    }
                }
            ]
        }
        try {
            const response = await fetch(BASE_URL + endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(query)
            })

            const transition = await response.json()
            this.latestProjects.push(...transition.hits.hits)
        } catch (error) {
            console.log(error)
        }
    },
    async findDocument(request) {
        try {
            const response = await fetch(BASE_URL + request, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                },
            })
            this.selectedDetailItem = await response.json()
            this.addRecentlyViewedItem(this.selectedDetailItem)
        } catch (error) {
            console.log(error)
        }
    },
    async sendCustomRequest(request) {
        this.spinner = true
        try {
            const response = await fetch(BASE_URL + request.endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(request.query)
            })

            const transition = await response.json()
            const hits = transition.hits.hits
            this.customResult.push(...hits)
            this.spinner = false
        } catch (error) {
            console.log(error)
            this.spinner = false
        }
    },
    async fetchStatistics(request) {
        try {
            const response = await fetch(BASE_URL + request.endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(request.query)
            })

            let transition = await response.json()
            this.stats[request.org] = transition.hits.total
        } catch (error) {
            console.log(error)
            this.spinner = false
        }
    },
    async fetchPersonsOfTheDay(endpoint) {
        const query = {
            query: {
                function_score: {
                    query: {match_all: {}},
                    random_score: {},
                    boost_mode: "replace"
                },
            },
            size: 3,
            _source: ["name", "title", "email", "homepage.url", "in.url"]
        }
        try {
            const response = await fetch(BASE_URL + endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(query)
            })

            const transition = await response.json()
            this.personsOfTheDay.push(...transition.hits.hits)
        } catch (error) {
            console.log(error)
        }
    },
    async fetchRelatedEntities(request){
        try {
            const response = await fetch(BASE_URL + request.endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(request.query)
            })

            const transition = await response.json()
            const hits = transition.hits.hits
            this.relatedEntities.push(...hits)
        } catch (error) {
            console.log(error)
        }
    },

    async fetchChildNodes(request){
        this.spinner = true
        try {
            const response = await fetch(BASE_URL + request, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                },
            })
            this.fetchedNode = await response.json()

        } catch (error) {
            console.log(error)
        }
    },
    async fetchRelatedNodes(request){
        this.spinner = true
        try {
            const response = await fetch(BASE_URL + request.endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(request.query)
            })

            const transition = await response.json()
            const hits = transition.hits.hits
            this.relatedNodes.push(...hits)
        } catch (error) {
            console.log(error)
        }
    },
}

const useElasticStore = defineStore('elasticStore', {
    state,
    getters,
    actions
});

export default useElasticStore